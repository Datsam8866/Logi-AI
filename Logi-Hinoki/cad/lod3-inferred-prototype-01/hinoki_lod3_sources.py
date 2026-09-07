"""Source-authority rules for the Hinoki LOD 3 inferred prototype."""

from types import MappingProxyType


SOURCE_PRECEDENCE = (
    "Known",
    "Derived",
    "DixieReference",
    "CompetitorOfficial",
    "EngineeringAssumption",
)

UNIFORM_DIXIE_SCALE_POLICY = MappingProxyType(
    {
        "parameter_id": "MP-077",
        "allowed": False,
        "reason": "Dixie 65-inch global coordinates must not be uniformly scaled.",
    }
)

PRIMARY_REFERENCES = MappingProxyType(
    {
        "HinokiParameters": "Hinoki_Master_Parameters_and_Assumption_Log.xlsx",
        "HinokiDixieTable": "Dixie and Hinoki table.xlsx",
        "DixieStep": "Dixie/3D/001_dixie65_set_asm_20250425_asm.stp",
        "DixieBom": "Dixie/BOM/logitech_Dixie65_Parts list_REV_20250506V1.xlsx",
        "NeatBoard32Product": "https://us.neat.no/board-32/?nr=US",
        "NeatBoard32DeviceSheet": (
            "https://cdn-stories.neat.no/1/2025/10/"
            "Neat_Board_32_Device_Sheet.pdf"
        ),
        "NeatBoard32Support": "https://support.neat.no/device/neat-board-32/",
    }
)


def resolve_candidates(parameter_name, candidates):
    """Choose the strongest source and preserve all rejected conflicts."""
    candidates = tuple(dict(candidate) for candidate in candidates)
    if not candidates:
        raise ValueError("No candidates for " + str(parameter_name))
    ranks = {source_class: index for index, source_class in enumerate(SOURCE_PRECEDENCE)}
    for candidate in candidates:
        source_class = candidate.get("source_class")
        if source_class not in ranks:
            raise ValueError("Unknown source class: " + str(source_class))
        if not candidate.get("source_reference"):
            raise ValueError("Candidate source_reference must be non-empty")
    top_rank = min(ranks[candidate["source_class"]] for candidate in candidates)
    strongest = [
        candidate
        for candidate in candidates
        if ranks[candidate["source_class"]] == top_rank
    ]
    top_values = {repr(candidate.get("value")) for candidate in strongest}
    if len(top_values) != 1:
        raise ValueError(
            "Conflicting equal-authority values for " + str(parameter_name)
        )
    selected = dict(strongest[0])
    selected["parameter_name"] = str(parameter_name)
    selected["rejected_candidates"] = tuple(
        dict(candidate) for candidate in candidates if candidate is not strongest[0]
    )
    return selected
