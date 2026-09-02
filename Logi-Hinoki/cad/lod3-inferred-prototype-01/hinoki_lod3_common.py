"""Shared FreeCAD helpers for the Hinoki LOD 3 prototype."""

import FreeCAD as App


def add_property(obj, property_type, name, value, group="Hinoki LOD3"):
    if name not in obj.PropertiesList:
        obj.addProperty(property_type, name, group)
    setattr(obj, name, value)


def add_metadata(obj, metadata):
    add_property(obj, "App::PropertyBool", "IsSemanticPart", True)
    string_keys = (
        "PartID",
        "PartName",
        "ParentAssembly",
        "MaterialIntent",
        "SourceClass",
        "SourceReference",
        "Confidence",
        "ThermalDisposition",
        "Revision",
    )
    for key in string_keys:
        add_property(obj, "App::PropertyString", key, str(metadata[key]))
    add_property(
        obj,
        "App::PropertyBool",
        "ManufacturingAuthority",
        bool(metadata["ManufacturingAuthority"]),
    )
    add_property(
        obj,
        "App::PropertyFloat",
        "HeatLoadW",
        float(metadata["HeatLoadW"]),
    )
    return obj


def semantic_part(doc, group, name, label, shape, metadata):
    obj = doc.addObject("Part::Feature", name)
    obj.Label = label
    obj.Shape = shape
    add_metadata(obj, metadata)
    group.addObject(obj)
    return obj


def centred_offset(outer, inner):
    return (float(outer) - float(inner)) / 2.0


def add_dimension(obj, name, value):
    add_property(obj, "App::PropertyLength", name, float(value))


def add_area(obj, name, value):
    add_property(obj, "App::PropertyArea", name, float(value))


def make_groups(doc, group_names):
    groups = {}
    for group_name in group_names:
        group = doc.addObject("App::DocumentObjectGroup", group_name)
        group.Label = group_name
        groups[group_name] = group
    return groups


def vector(x, y, z):
    return App.Vector(float(x), float(y), float(z))
