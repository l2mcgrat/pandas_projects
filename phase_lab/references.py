"""Small, attributed reference dataset; never invent an empirical potential energy.

Room-temperature densities are initialization anchors, not a 300 K equation of
state. Source pressure is not specified; ambient pressure is an assumption.
"""

REFERENCE_VERSION = "room-temperature-v1"
DENSITIES = {
    "glycerol": (1.2613, 293.15, "753", "CRC Handbook, 88th ed., via PubChem/HSDB"),
    "ethylene_glycol": (1.1135, 293.15, "174", "CRC Handbook, 91st ed., via PubChem/HSDB"),
    "dmso": (1.100, 293.15, "679", "Merck Index (2013), via PubChem/HSDB; relative density 20/4 C"),
    "propylene_glycol": (1.0361, 293.15, "1030", "CRC Handbook, 88th ed., via PubChem/HSDB"),
    "formamide": (1.1334, 293.15, "713", "Merck Index (1996), via PubChem/HSDB; relative density 20/4 C"),
    "benzyl_alcohol": (1.0419, 297.15, "244", "CRC Handbook, 94th ed., via PubChem/HSDB"),
}

# Sparse literature observations, not an interpolatable T/P energy table.
VAPORIZATION = {
    "dmso": {"value": 51.7, "temperature_K": 320., "pressure_kPa": None,
             "source": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C67685&Mask=4",
             "citation": "Stephenson and Malanowski (1987), NIST WebBook; based on 305–464 K data"},
    "ethylene_glycol": {"value": 62.4, "uncertainty_kJ_mol": 4.0, "temperature_K": 345., "pressure_kPa": None,
                        "source": "https://webbook.nist.gov/cgi/cbook.cgi?ID=C107211&Mask=4",
                        "citation": "Petitjean, Reyes-Perez et al. (2010), via NIST WebBook; 62.4 +/- 4.0 kJ/mol at 345 K, based on 307-384 K data"},
    "benzyl_alcohol": {"value": 50.48, "temperature_K": 478.46, "pressure_kPa": 101.325,
                       "source": "https://pubchem.ncbi.nlm.nih.gov/compound/244#section=Heat-of-Vaporization",
                       "citation": "CRC Handbook, 94th ed., via PubChem/HSDB: normal boiling point 205.31 C"},
}


def density_reference(name):
    value, temperature, cid, citation = DENSITIES[name]
    return {"value_g_cm3": value, "temperature_K": temperature, "pressure_kPa": None,
            "source": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}#section=Density",
            "citation": citation, "note": "Room-temperature anchor; not an exact 300 K / 1 atm measurement."}


def empirical_comparison(name, temperature, pressure):
    reference = VAPORIZATION.get(name)
    return {"potential_kJ_mol": None,
            "reason": "No measured absolute potential energy with this model's reference zero at the selected T/P.",
            "selected_temperature_K": float(temperature),
            "selected_pressure_kPa": float(pressure) if pressure else None,
            "density": density_reference(name), "vaporization": reference,
            "matched_vaporization_TP": bool(reference and pressure
                and abs(float(temperature) - reference["temperature_K"]) < .05
                and reference["pressure_kPa"] is not None
                and abs(float(pressure) - reference["pressure_kPa"]) < .05)}