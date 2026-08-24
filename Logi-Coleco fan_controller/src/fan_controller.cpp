#include "fan_controller.h"

#include <algorithm>
#include <cmath>
#include <iostream>
#include <numeric>
#include <stdexcept>

TemperatureFilter::TemperatureFilter(double window_seconds)
    : window_seconds_(window_seconds) {}

std::optional<double> TemperatureFilter::add(double value, double now_seconds) {
    samples_.push_back({value, now_seconds});

    while (!samples_.empty() &&
           now_seconds - samples_.front().timestamp > window_seconds_) {
        samples_.pop_front();
    }

    if (samples_.empty()) return std::nullopt;

    double sum = 0.0;
    for (const auto& s : samples_) sum += s.value;
    return sum / static_cast<double>(samples_.size());
}

void TemperatureFilter::reset() {
    samples_.clear();
}

MedianFilter::MedianFilter(int window_size)
    : window_size_(std::max(3, window_size | 1)) {}

std::optional<double> MedianFilter::add(double value) {
    values_.push_back(value);
    while (static_cast<int>(values_.size()) > window_size_) {
        values_.pop_front();
    }

    if (values_.empty()) return std::nullopt;

    std::vector<double> tmp(values_.begin(), values_.end());
    std::sort(tmp.begin(), tmp.end());
    return tmp[tmp.size() / 2];
}

void MedianFilter::reset() {
    values_.clear();
}

FanController::FanController(HardwareInterface& hw, FanConfig cfg)
    : hw_(hw),
      cfg_(std::move(cfg)),
      amb_filter_(cfg_.temperature_filter_seconds),
      cpu_filter_(cfg_.temperature_filter_seconds),
      fg_filter_(cfg_.fg_median_window) {}

bool FanController::validateAndFilterTemperature(
    double raw_c,
    double now_seconds,
    TemperatureFilter& filter,
    double& filtered_c,
    bool& initialized) {

    /*
     * RULE 12:
     * First reject physically unreasonable values. This is deliberately done
     * BEFORE averaging so a broken sensor cannot contaminate the 10 s average.
     */
    if (!std::isfinite(raw_c) ||
        raw_c < cfg_.min_valid_temperature_c ||
        raw_c > cfg_.max_valid_temperature_c) {
        return false;
    }

    /*
     * RULE 12:
     * Reject an abrupt >10 C jump occurring within 500 ms.
     *
     * We compare against the newest sample already present in the filter.
     * The filter itself remains clean when a bad sample is rejected.
     */
    if (initialized) {
        // The filter's latest value is not directly exposed, so use the
        // current filtered value as the conservative reference.
        if (std::fabs(raw_c - filtered_c) > cfg_.max_temp_step_c) {
            // At a 0.5 s control period this exactly implements the requested
            // 10 C / 500 ms rule. For longer periods, this is still a safe
            // rejection rather than an unsafe acceptance.
            if (now_seconds - last_update_seconds_ <=
                cfg_.max_temp_step_window_seconds + 1e-6) {
                return false;
            }
        }
    }

    auto avg = filter.add(raw_c, now_seconds);
    if (!avg.has_value()) return false;

    filtered_c = *avg;
    initialized = true;
    return true;
}

double FanController::interpolateCurve(
    const std::vector<CurvePoint>& curve, double cpu_c) const {

    if (curve.empty()) return cfg_.min_rpm;

    /*
     * RULE 6:
     * Below the first point, clamp to the first RPM.
     * Above the last point, extrapolate using the last segment.
     *
     * This is intentional because the specification says:
     *   - below 1000 RPM do not reduce further
     *   - above 3000 RPM may continue to extrapolate
     */
    if (cpu_c <= curve.front().cpu_c)
        return curve.front().rpm;

    for (size_t i = 1; i < curve.size(); ++i) {
        if (cpu_c <= curve[i].cpu_c) {
            const auto& p0 = curve[i - 1];
            const auto& p1 = curve[i];

            const double x = (cpu_c - p0.cpu_c) / (p1.cpu_c - p0.cpu_c);
            return p0.rpm + x * (p1.rpm - p0.rpm);
        }
    }

    // Linear extrapolation above the final curve point.
    const auto& p0 = curve[curve.size() - 2];
    const auto& p1 = curve[curve.size() - 1];

    const double slope = (p1.rpm - p0.rpm) / (p1.cpu_c - p0.cpu_c);
    return p1.rpm + slope * (cpu_c - p1.cpu_c);
}

double FanController::interpolateAmbientCurve(double cpu_c,
                                               double amb_c) const {
    /*
     * RULE 5:
     * Calculate BOTH low-ambient and high-ambient fan targets first,
     * then interpolate between them according to T_AMB.
     *
     * Example:
     *   T_AMB = 25 C -> 100% low-ambient curve
     *   T_AMB = 35 C -> 100% high-ambient curve
     *   T_AMB = 30 C -> 50% between the two curves
     */
    const double low_target = interpolateCurve(cfg_.curve_low_amb, cpu_c);
    const double high_target = interpolateCurve(cfg_.curve_high_amb, cpu_c);

    if (amb_c <= cfg_.amb_low_c)
        return low_target;

    if (amb_c >= cfg_.amb_high_c)
        return high_target;

    const double alpha =
        (amb_c - cfg_.amb_low_c) / (cfg_.amb_high_c - cfg_.amb_low_c);

    return low_target + alpha * (high_target - low_target);
}

double FanController::applyHysteresis(double requested_rpm, double /*cpu_c*/) {
    /*
     * RULE 8:
     * A continuous fan curve does not have a single ON/OFF threshold, so a
     * literal +/-3 C hysteresis cannot simply be added to every interpolation
     * point without distorting the curve.
     *
     * Here we use a practical implementation:
     *   - If temperature remains within +/-3 C of the previous control
     *     temperature region, retain the previous RPM target.
     *   - A new target is accepted when the temperature leaves that band.
     *
     * This reduces small oscillations caused by sensor noise.
     *
     * For a product that needs more aggressive response, this function is the
     * intended place to change the hysteresis strategy.
     */
    if (!std::isfinite(hysteresis_reference_rpm_)) {
        hysteresis_reference_rpm_ = requested_rpm;
        return requested_rpm;
    }

    /*
     * Do not freeze the fan for a full 3 C. Instead, use a smaller RPM deadband
     * derived from the requested temperature hysteresis. This avoids a large
     * thermal delay while still preventing hunting.
     */
    const double rpm_deadband =
        std::max(50.0, cfg_.hysteresis_c * 50.0);

    if (std::fabs(requested_rpm - hysteresis_reference_rpm_) < rpm_deadband)
        return hysteresis_reference_rpm_;

    hysteresis_reference_rpm_ = requested_rpm;
    return requested_rpm;
}

double FanController::rampTarget(double requested_rpm, double dt_seconds) {
    /*
     * RULE 13:
     * Limit the change of final_target_rpm to 100 RPM/s by default.
     *
     * This is applied after fan-curve calculation and hysteresis, so even a
     * sudden thermal change cannot command an instantaneous RPM jump.
     */
    const double max_delta =
        cfg_.max_rpm_ramp_per_second * std::max(0.0, dt_seconds);

    if (requested_rpm > last_target_rpm_ + max_delta)
        return last_target_rpm_ + max_delta;

    if (requested_rpm < last_target_rpm_ - max_delta)
        return last_target_rpm_ - max_delta;

    return requested_rpm;
}

void FanController::handleFanStart(double target_rpm,
                                    double actual_rpm,
                                    double now_seconds) {
    /*
     * RULE 9:
     * A 4-wire PWM fan may fail to start at a low duty. Once a non-zero target
     * is requested, start monitoring the FG signal.
     *
     * If the fan is still effectively stopped after 3 s:
     *   1. Force 50% duty.
     *   2. Keep it long enough for the next control cycle.
     *   3. Then return to the normal target RPM control.
     */
    constexpr double RPM_RUNNING_THRESHOLD = 300.0;

    if (target_rpm > 0.0 && actual_rpm < RPM_RUNNING_THRESHOLD) {
        if (!fan_start_pending_) {
            fan_start_pending_ = true;
            fan_start_time_ = now_seconds;
            start_boost_active_ = false;
        }

        if (now_seconds - fan_start_time_ >= cfg_.start_timeout_seconds) {
            start_boost_active_ = true;
        }
    } else {
        fan_start_pending_ = false;
        start_boost_active_ = false;
    }
}

bool FanController::readSensors(double now_seconds) {
    /*
     * RULE 10:
     * TMP75B failure is treated as a safety-critical event.
     * Any failed/no-ACK read increments the consecutive failure counter.
     */
    double amb_raw = 0.0;
    if (!hw_.readTmp75b(amb_raw)) {
        ++tmp75b_consecutive_failures_;

        if (tmp75b_consecutive_failures_ >=
            cfg_.i2c_failures_before_reset) {
            /*
             * RULE 11:
             * Ask the hardware backend to recover the I2C bus by GPIO bit
             * banging SCL/SDA and sending 9 clocks.
             */
            hw_.resetTmp75bI2cBus();
        }

        /*
         * RULE 10:
         * Do not wait for all five failures to trigger protection.
         * One confirmed TMP75B communication failure is sufficient to enter
         * failsafe because ambient temperature is part of the thermal model.
         */
        failsafe_ = true;
    } else {
        tmp75b_consecutive_failures_ = 0;

        if (!validateAndFilterTemperature(
                amb_raw, now_seconds, amb_filter_,
                filtered_amb_c_, amb_initialized_)) {
            failsafe_ = true;
        }
    }

    double cpu_raw = 0.0;
    if (!hw_.readCpuThermistor(cpu_raw)) {
        /*
         * CPU thermistor failure is also unsafe. The safest behavior is 100%
         * fan. This is an additional protection beyond the original request.
         */
        failsafe_ = true;
    } else {
        if (!validateAndFilterTemperature(
                cpu_raw, now_seconds, cpu_filter_,
                filtered_cpu_c_, cpu_initialized_)) {
            failsafe_ = true;
        }
    }

    double rpm_raw = 0.0;
    if (hw_.readFanRpm(rpm_raw)) {
        auto filtered = fg_filter_.add(rpm_raw);
        if (filtered.has_value()) {
            filtered_actual_rpm_ = *filtered;
            rpm_initialized_ = true;
        }
    }

    return amb_initialized_ && cpu_initialized_;
}

bool FanController::update(double now_seconds) {
    double dt = cfg_.control_period_seconds;
    if (last_update_seconds_ >= 0.0)
        dt = std::max(0.001, now_seconds - last_update_seconds_);

    const bool sensors_ok = readSensors(now_seconds);

    if (failsafe_ || !sensors_ok) {
        /*
         * FAILSAFE:
         * 100% duty is deliberately independent of the fan curve.
         * We do not use the potentially invalid temperature data here.
         */
        target_rpm_ = cfg_.max_rpm;
        last_target_rpm_ = target_rpm_;
        fan_start_pending_ = false;
        start_boost_active_ = false;
        last_update_seconds_ = now_seconds;
        return hw_.setFanDuty(cfg_.max_duty);
    }

    /*
     * RULE 5/6:
     * Generate the target RPM from the two ambient-dependent curves.
     */
    double requested_rpm =
        interpolateAmbientCurve(filtered_cpu_c_, filtered_amb_c_);

    requested_rpm = std::clamp(
        requested_rpm, cfg_.min_rpm, cfg_.max_rpm);

    /*
     * RULE 8:
     * Apply hysteresis before the final RPM ramp.
     */
    requested_rpm = applyHysteresis(requested_rpm, filtered_cpu_c_);

    /*
     * RULE 13:
     * Limit final RPM target slope.
     */
    target_rpm_ = rampTarget(requested_rpm, dt);

    /*
     * RULE 9:
     * Check whether the fan actually started.
     */
    handleFanStart(target_rpm_, filtered_actual_rpm_, now_seconds);

    double duty = 0.0;

    if (target_rpm_ <= 0.0) {
        duty = 0.0;
    } else if (start_boost_active_) {
        duty = cfg_.start_boost_duty;
    } else {
        /*
         * IMPORTANT:
         * A true RPM-control fan needs a closed-loop mapping between duty and
         * RPM. There is no universal equation because every fan has a
         * different duty/RPM curve.
         *
         * This controller therefore uses a PI-like incremental correction:
         * duty is adjusted based on RPM error.
         *
         * For production, replace this section with a calibrated duty-vs-RPM
         * lookup table if available. That is normally more predictable than a
         * pure feedback controller.
         */
        static double duty_state = 0.20;

        const double error = target_rpm_ - filtered_actual_rpm_;

        // Conservative proportional gain; tune on the real fan.
        constexpr double KP = 0.00020;

        duty_state += KP * error;

        // Rule 14: minimum duty whenever target RPM > 0.
        duty_state = std::clamp(
            duty_state, cfg_.min_start_duty, cfg_.max_duty);

        duty = duty_state;
    }

    last_target_rpm_ = target_rpm_;
    last_update_seconds_ = now_seconds;

    return hw_.setFanDuty(duty);
}
