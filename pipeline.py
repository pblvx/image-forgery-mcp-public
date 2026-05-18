import json
import subprocess
from pathlib import Path
from typing import Any

from ..schemas import MetadataResult, MetadataFinding


def analyze_metadata(image_path: Path, sha256: str) -> MetadataResult:
    """Analyze image metadata using exiftool."""
    cmd = ["exiftool", "-j", str(image_path)]
    data: dict[str, Any] = {}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        parsed = json.loads(proc.stdout)
        if isinstance(parsed, list) and len(parsed) > 0:
            data = parsed[0]
    except Exception:
        # Fallback to empty if exiftool fails or is missing
        pass

    # Basic detection heuristics
    keys = list(data.keys())
    exif_present = any(k.startswith("EXIF:") for k in keys) or "DateTimeOriginal" in keys or "Make" in keys
    xmp_present = any(k.startswith("XMP:") for k in keys)
    
    software = data.get("Software")
    if not isinstance(software, str):
        software = None
        
    creation_date = data.get("DateTimeOriginal", data.get("CreateDate"))
    if not isinstance(creation_date, str):
        creation_date = None
        
    modification_date = data.get("ModifyDate")
    if not isinstance(modification_date, str):
        modification_date = None
        
    dpi_val = data.get("XResolution")
    dpi = int(dpi_val) if isinstance(dpi_val, (int, float, str)) and str(dpi_val).isdigit() else None
    
    color_space = data.get("ColorSpace")
    if not isinstance(color_space, str):
        color_space = None
        
    findings = []
    metadata_risk_score = 0.0
    
    if software and any(name in software.lower() for name in ['photoshop', 'gimp', 'lightroom', 'illustrator']):
        findings.append(MetadataFinding(
            type="editing_software_detected",
            severity="medium",
            description="Metadatos EXIF indican exportación desde software de edición",
            evidence=f"Software={software}",
            interpretation="Indica posible edición. No prueba falsificación."
        ))
        metadata_risk_score += 0.3
        
    if creation_date and modification_date and creation_date > modification_date:
        findings.append(MetadataFinding(
            type="timestamp_inconsistency",
            severity="medium",
            description="Fecha de modificación anterior a fecha de creación",
            evidence=f"DateTime={modification_date} < DateTimeOriginal={creation_date}",
            interpretation="Posible edición de metadatos o reloj incorrecto en el dispositivo."
        ))
        metadata_risk_score += 0.3
        
    metadata_risk_score = min(metadata_risk_score, 1.0)
    
    return MetadataResult(
        exif_present=exif_present,
        xmp_present=xmp_present,
        software=software,
        creation_date=creation_date,
        modification_date=modification_date,
        dpi=dpi,
        color_space=color_space,
        metadata_risk_score=metadata_risk_score,
        findings=findings,
        limitations=[
            "La presencia de software de edición no prueba falsificación.",
            "Los metadatos pueden ser borrados o modificados trivialmente fácilmente."
        ]
    )
