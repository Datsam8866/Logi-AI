#pragma once
/*
 * QCS8550 Fan Controller
 *
 * Purpose:
 *   - Read T_AMB from TMP75B over I2C.
 *   - Read T_CPU from a board thermistor/ADC.
 *   - Interpolate between low/high ambient fan curves.
 *   - Filter temperatures, reject impossible jumps, and apply hysteresis.
 *   - Control a 4-wire PWM fan using RPM feedback.
 *   - Apply RPM ramping, minimum start duty, start boost, FG median filtering.
 *   - Enter 100% duty failsafe when TMP75B is unavailable.
 *
 * IMPORTANT:
 *   This file intentionally contains no Qualcomm/Thundercomm-specific GPIO,
 *   PWM, ADC or I2C device numbers. Those are board-specific and must be
 *   supplied by the Linux/Android HAL/backend.
 */

#include <cstdint>
#include <deque>
#include <optional>
#include <string>
#include <vector>

struct CurvePoint {
    double cpu_c;
    double rpm;
};

struct FanConfig {
    // Fan curve data from the specification.
    std::vector<CurvePoint> curve_low_amb{
        {35.0, 1000.0}, {40.0, 1500.0}, {46.0, 2000.0}
    };
    std::vector<CurvePoint> curve_high_amb{
        {35.0, 2000.0}, {40.0, 2500.0}, {46.0, 3000.0}
    };

    double amb_low_c = 25.0;
    double amb_high_c = 35.0;

    double min_rpm = 1000.0;
    double max_rpm = 6000.0;          // Safety/configuration ceiling.
    double max_duty = 1.0;
    double min_start_duty = 0.20;

    // Rule 7: 10-second moving average.
    double temperature_filter_seconds = 10.0;

    // Rule 8: temperature hysteresis.
    double hysteresis_c = 3.0;

    // Rule 9: 3 s start detection and 50% recovery duty.
    double start_timeout_seconds = 3.0;
    double start_boost_duty = 0.50;

    // Rule 11: I2C recovery after 5 consecutive failures.
    int i2c_failures_before_reset = 5;

    // Rule 12: reject >10 C change in 500 ms.
    double max_temp_step_c = 10.0;
    double max_temp_step_window_seconds = 0.5;

    // Rule 13: RPM target ramping.
    double max_rpm_ramp_per_second = 100.0;

    // Rule 16: FG median filter.
    int fg_median_window = 5;

    // Safety limits.
    double min_valid_temperature_c = -40.0;
    double max_valid_temperature_c = 125.0;

    // Main loop period.
    double control_period_seconds = 0.5;
};

struct SensorSample {
    double temperature_c;
    bool valid;
};

class TemperatureFilter {
public:
    explicit TemperatureFilter(double window_seconds);
    std::optional<double> add(double value, double now_seconds);
    void reset();

private:
    struct Sample {
        double value;
        double timestamp;
    };
    double window_seconds_;
    std::deque<Sample> samples_;
};

class MedianFilter {
public:
    explicit MedianFilter(int window_size);
    std::optional<double> add(double value);
    void reset();

private:
    int window_size_;
    std::deque<double> values_;
};

class HardwareInterface {
public:
    virtual ~HardwareInterface() = default;

    // TMP75B temperature, degrees C.
    virtual bool readTmp75b(double& temperature_c) = 0;

    // Board thermistor converted to degrees C.
    virtual bool readCpuThermistor(double& temperature_c) = 0;

    // Actual fan RPM from FG/tachometer.
    virtual bool readFanRpm(double& rpm) = 0;

    // PWM duty: 0.0 ... 1.0.
    virtual bool setFanDuty(double duty) = 0;

    // Must recover an I2C bus which is stuck low.
    virtual bool resetTmp75bI2cBus() = 0;
};

class FanController {
public:
    FanController(HardwareInterface& hw, FanConfig cfg);

    // Call once every cfg.control_period_seconds.
    bool update(double now_seconds);

    bool inFailsafe() const { return failsafe_; }
    double targetRpm() const { return target_rpm_; }
    double filteredAmb() const { return filtered_amb_c_; }
    double filteredCpu() const { return filtered_cpu_c_; }
    double filteredActualRpm() const { return filtered_actual_rpm_; }

private:
    double interpolateCurve(const std::vector<CurvePoint>& curve,
                            double cpu_c) const;

    double interpolateAmbientCurve(double cpu_c, double amb_c) const;

    bool validateAndFilterTemperature(double raw_c,
                                      double now_seconds,
                                      TemperatureFilter& filter,
                                      double& filtered_c,
                                      bool& initialized);

    double applyHysteresis(double requested_rpm, double cpu_c);

    double rampTarget(double requested_rpm, double dt_seconds);

    void handleFanStart(double target_rpm,
                        double actual_rpm,
                        double now_seconds);

    bool readSensors(double now_seconds);

    HardwareInterface& hw_;
    FanConfig cfg_;

    TemperatureFilter amb_filter_;
    TemperatureFilter cpu_filter_;
    MedianFilter fg_filter_;

    bool amb_initialized_ = false;
    bool cpu_initialized_ = false;
    bool rpm_initialized_ = false;

    double filtered_amb_c_ = 0.0;
    double filtered_cpu_c_ = 0.0;
    double filtered_actual_rpm_ = 0.0;

    double target_rpm_ = 0.0;
    double last_target_rpm_ = 0.0;
    double last_update_seconds_ = -1.0;

    bool failsafe_ = false;
    int tmp75b_consecutive_failures_ = 0;

    bool fan_start_pending_ = false;
    double fan_start_time_ = 0.0;
    bool start_boost_active_ = false;

    // State used by temperature hysteresis.
    double hysteresis_reference_rpm_ = 0.0;
};
