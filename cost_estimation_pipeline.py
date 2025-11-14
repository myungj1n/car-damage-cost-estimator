"""
Complete Cost Estimation Pipeline
VIN → Vehicle ID → Part Detection → Damage Assessment → Cost Calculation
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any

# ============================================================
# CONSTANTS
# ============================================================
LABOR_RATE = 55  # $/hour
SALES_TAX = 1.06  # 6%

# Damage type to action mapping
DAMAGE_ACTION_MAP = {
    'Scratch': 'repair',
    'Dent': 'repair',
    'Crack': 'replace',
    'Glass shatter': 'replace',
    'Lamp broken': 'replace',
    'Tear': 'replace',
    'Broken': 'replace',
    'Missing': 'replace'
}

# ML class to OEM part description mapping
ML_CLASS_TO_OEM_PARTS = {
    'Front-bumper': ['bumper', 'front bumper', 'bumper cover front'],
    'Back-bumper': ['rear bumper', 'back bumper', 'bumper cover rear'],
    'Hood': ['hood', 'hood panel'],
    'Front-door': ['front door', 'door front', 'door shell front'],
    'Back-door': ['rear door', 'back door', 'door shell rear'],
    'Trunk': ['trunk', 'deck lid', 'trunk lid'],
    'Fender': ['fender', 'front fender'],
    'Quarter-panel': ['quarter panel', 'quarter', 'rear quarter'],
    'Rocker-panel': ['rocker panel', 'rocker'],
    'Running-board': ['running board', 'step', 'side step'],
    'Headlamp': ['headlight', 'headlamp', 'head lamp'],
    'Tail-lamp': ['tail light', 'tail lamp', 'rear lamp'],
    'Front-windshield': ['windshield', 'front windshield'],
    'Back-windshield': ['rear windshield', 'back windshield', 'rear window'],
    'Front-sideview-mirror': ['mirror', 'side mirror', 'door mirror'],
    'Wheel': ['wheel', 'rim'],
    'Roof': ['roof', 'roof panel'],
    'Grille': ['grille', 'grill', 'front grille'],
    'Door-handle': ['door handle', 'handle'],
    'Fog-lamp': ['fog light', 'fog lamp'],
    'License-plate': ['license plate', 'plate bracket']
}

# ML class to labor hours part name mapping
ML_CLASS_TO_LABOR_PART = {
    'Front-bumper': 'Front-bumper',
    'Back-bumper': 'Back-bumper',
    'Hood': 'Hood',
    'Front-door': 'Front-door',
    'Back-door': 'Back-door',
    'Trunk': 'Trunk',
    'Fender': 'Fender',
    'Quarter-panel': 'Quarter-panel',
    'Rocker-panel': 'Rocker-panel',
    'Running-board': 'Rocker-panel',  # Use rocker panel hours
    'Headlamp': 'Headlight',
    'Tail-lamp': 'Tail-light',
    'Front-windshield': 'Windshield',
    'Back-windshield': 'Back-windshield',
    'Front-sideview-mirror': 'Mirror',
    'Wheel': 'Front-wheel',  # Average of front/back
    'Roof': 'Roof',
    'Grille': 'Grille',
    'Door-handle': 'Front-door',  # Use door hours as proxy
    'Fog-lamp': 'Headlight',  # Use headlight hours as proxy
    'License-plate': 'License-plate'
}


# ============================================================
# STEP 1: VIN DECODING
# ============================================================

def decode_vin_from_dataset(vin: str) -> Dict[str, Any]:
    """
    Decode VIN using the VIN dataset
    Returns vehicle information or None if not found
    """
    vin_df = pd.read_csv('vin_dataset.csv')
    
    # Try exact match first
    vehicle_match = vin_df[vin_df['VIN'] == vin]
    
    if vehicle_match.empty:
        # Try partial matching (first 11 chars = WMI + VDS)
        vin_prefix = vin[:11]
        vehicle_match = vin_df[vin_df['VIN'].str.startswith(vin_prefix)]
    
    if not vehicle_match.empty:
        return {
            'make': vehicle_match.iloc[0]['Make'],
            'model': vehicle_match.iloc[0]['Model'],
            'year': vehicle_match.iloc[0]['Year'],
        }
    
    return None


# ============================================================
# STEP 2: VEHICLE-SPECIFIC PART FILTERING
# ============================================================

def get_available_parts_for_vehicle(vehicle_info: Dict) -> Tuple[List[str], pd.DataFrame]:
    """
    Get parts available for this specific vehicle from OEM database
    Returns: (available_classes, vehicle_parts_dataframe)
    """
    oem_df = pd.read_csv('oem_parts_data.csv')
    
    # Filter by make (case-insensitive)
    vehicle_parts = oem_df[
        oem_df['Make'].str.upper() == vehicle_info['make'].upper()
    ]
    
    # Get unique part types available
    available_part_descriptions = vehicle_parts['Part Description'].unique()
    
    # Map to ML classes
    available_classes = []
    for ml_class, search_terms in ML_CLASS_TO_OEM_PARTS.items():
        # Check if any OEM part matches this ML class
        for desc in available_part_descriptions:
            if any(term in desc.lower() for term in search_terms):
                available_classes.append(ml_class)
                break
    
    return available_classes, vehicle_parts


# ============================================================
# STEP 3: PART DETECTION & DAMAGE ASSESSMENT
# ============================================================

def detect_parts_and_damage(image, part_model, damage_model, available_classes: List[str]) -> List[Dict]:
    """
    Run both models on image and combine results
    
    Args:
        image: Input image (numpy array or PIL Image)
        part_model: Trained part identification model
        damage_model: Trained damage classification model
        available_classes: List of part classes valid for this vehicle
    
    Returns:
        List of detected parts with damage assessment
    """
    # Run part identification model
    # Expected output: dict of {class_name: probability}
    all_part_predictions = part_model.predict(image)
    
    # Filter to available classes and apply threshold
    detected_parts = [
        (part_class, prob)
        for part_class, prob in all_part_predictions.items()
        if part_class in available_classes and prob > 0.70
    ]
    
    if not detected_parts:
        return []
    
    # Run damage classification model
    # Expected output: dict of {damage_type: probability}
    damage_predictions = damage_model.predict(image)
    
    # Filter damages above threshold
    detected_damages = [
        (damage_type, prob)
        for damage_type, prob in damage_predictions.items()
        if prob > 0.60
    ]
    
    # Determine action based on damage types
    action = determine_action(detected_damages)
    
    # Combine results
    detections = []
    for part_class, part_confidence in detected_parts:
        detections.append({
            'part': part_class,
            'part_confidence': part_confidence,
            'damage_types': detected_damages,
            'action': action
        })
    
    return detections


def determine_action(damage_assessment: List[Tuple[str, float]]) -> str:
    """
    Determine if part should be repaired or replaced
    If ANY damage requires replacement, return 'replace'
    """
    actions = [
        DAMAGE_ACTION_MAP[damage_type]
        for damage_type, _ in damage_assessment
        if damage_type in DAMAGE_ACTION_MAP
    ]
    
    if 'replace' in actions:
        return 'replace'
    elif 'repair' in actions:
        return 'repair'
    else:
        return 'repair'  # Default to repair if unclear


# ============================================================
# STEP 4: CONSOLIDATE MULTI-IMAGE DETECTIONS
# ============================================================

def consolidate_detections(all_detections: List[Dict]) -> List[Dict]:
    """
    Consolidate detections from multiple images
    - Take highest confidence for each part
    - Take worst damage (replace > repair)
    """
    part_dict = {}
    
    for detection in all_detections:
        part = detection['part']
        
        if part not in part_dict:
            part_dict[part] = detection
        else:
            existing = part_dict[part]
            
            # Keep higher confidence
            if detection['part_confidence'] > existing['part_confidence']:
                part_dict[part]['part_confidence'] = detection['part_confidence']
            
            # Keep worse damage (replace > repair)
            if detection['action'] == 'replace':
                part_dict[part]['action'] = 'replace'
            
            # Merge damage types (take maximum confidence for each type)
            existing_damages = {d: c for d, c in existing['damage_types']}
            new_damages = {d: c for d, c in detection['damage_types']}
            
            all_damage_types = set(existing_damages.keys()) | set(new_damages.keys())
            combined_damages = [
                (damage_type, max(existing_damages.get(damage_type, 0), 
                                 new_damages.get(damage_type, 0)))
                for damage_type in all_damage_types
            ]
            
            part_dict[part]['damage_types'] = combined_damages
    
    return list(part_dict.values())


# ============================================================
# STEP 5: COST CALCULATION
# ============================================================

def find_matching_oem_parts(part_class: str, vehicle_parts_df: pd.DataFrame) -> pd.DataFrame:
    """
    Find OEM parts that match the ML-detected class
    """
    search_terms = ML_CLASS_TO_OEM_PARTS.get(part_class, [])
    
    if not search_terms:
        return pd.DataFrame()
    
    # Search in part descriptions (case-insensitive)
    mask = vehicle_parts_df['Part Description'].str.lower().str.contains(
        '|'.join(search_terms),
        case=False,
        na=False,
        regex=True
    )
    
    return vehicle_parts_df[mask]


def get_labor_hours(part_class: str) -> Dict[str, float]:
    """
    Get labor hours for repair and replacement from labor_hours.csv
    """
    labor_df = pd.read_csv('labor_hours.csv')
    
    # Map ML class to labor hours part name
    labor_part_name = ML_CLASS_TO_LABOR_PART.get(part_class)
    
    if not labor_part_name:
        # Default hours if mapping not found
        return {'repair_hours': 2.0, 'replacement_hours': 3.0}
    
    # Find matching row
    matching_row = labor_df[labor_df['Part'] == labor_part_name]
    
    if matching_row.empty:
        return {'repair_hours': 2.0, 'replacement_hours': 3.0}
    
    return {
        'repair_hours': float(matching_row['Repair_Hours'].iloc[0]),
        'replacement_hours': float(matching_row['Replace_Hours'].iloc[0])
    }


def calculate_part_cost(part_class: str, action: str, oem_parts_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate cost for one part (repair or replacement)
    
    Returns dict with:
        - oem_price (if replace)
        - labor_hours
        - labor_cost
        - subtotal
        - total_with_tax
    """
    labor_info = get_labor_hours(part_class)
    
    if action == 'replace':
        # Get OEM price
        if oem_parts_df.empty:
            oem_price = None
            parts_cost = 0
        else:
            oem_price = oem_parts_df['Price'].mean()
            parts_cost = oem_price
        
        labor_hours = labor_info['replacement_hours']
        labor_cost = LABOR_RATE * labor_hours
        subtotal = parts_cost + labor_cost
        total_with_tax = subtotal * SALES_TAX
        
        return {
            'action': 'Replace',
            'oem_price': oem_price,
            'labor_hours': labor_hours,
            'labor_cost': labor_cost,
            'subtotal': subtotal,
            'total_with_tax': total_with_tax,
            'has_oem_data': not oem_parts_df.empty
        }
    
    else:  # repair
        labor_hours = labor_info['repair_hours']
        labor_cost = LABOR_RATE * labor_hours
        total_with_tax = labor_cost * SALES_TAX
        
        return {
            'action': 'Repair',
            'oem_price': None,
            'labor_hours': labor_hours,
            'labor_cost': labor_cost,
            'subtotal': labor_cost,
            'total_with_tax': total_with_tax,
            'has_oem_data': True  # Not needed for repair
        }


# ============================================================
# MAIN PIPELINE
# ============================================================

def estimate_repair_cost(vin: str, images: List, part_model, damage_model) -> Dict[str, Any]:
    """
    Complete pipeline: VIN → Vehicle → Parts → Damage → Cost
    
    Args:
        vin: 17-character VIN string
        images: List of images (numpy arrays or PIL Images)
        part_model: Trained part identification model
        damage_model: Trained damage classification model
    
    Returns:
        Complete repair estimate with breakdown
    """
    # STEP 1: Decode VIN
    vehicle_info = decode_vin_from_dataset(vin)
    if not vehicle_info:
        return {"error": "VIN not found in database"}
    
    # STEP 2: Get available parts for this vehicle
    available_classes, vehicle_parts_df = get_available_parts_for_vehicle(vehicle_info)
    
    if not available_classes:
        return {"error": f"No OEM parts data for {vehicle_info['make']}"}
    
    # STEP 3: Process each image
    all_detections = []
    
    for idx, image in enumerate(images):
        detections = detect_parts_and_damage(
            image, 
            part_model, 
            damage_model, 
            available_classes
        )
        
        # Add image index to each detection
        for detection in detections:
            detection['image_idx'] = idx
        
        all_detections.extend(detections)
    
    if not all_detections:
        return {
            "vehicle": vehicle_info,
            "message": "No damaged parts detected in images"
        }
    
    # STEP 4: Consolidate detections across images
    consolidated_parts = consolidate_detections(all_detections)
    
    # STEP 5: Calculate costs
    repair_estimate = []
    total_cost = 0
    
    for detection in consolidated_parts:
        part_class = detection['part']
        action = detection['action']
        
        # Find matching OEM parts
        matching_parts = find_matching_oem_parts(part_class, vehicle_parts_df)
        
        # Calculate cost
        cost_info = calculate_part_cost(part_class, action, matching_parts)
        
        # Build repair item
        repair_item = {
            'part': part_class,
            'action': cost_info['action'],
            'damage_detected': [d for d, c in detection['damage_types']],
            'confidence': f"{detection['part_confidence']:.1%}",
            'labor_hours': cost_info['labor_hours'],
            'labor_cost': f"${cost_info['labor_cost']:.2f}",
        }
        
        if cost_info['oem_price'] is not None:
            repair_item['oem_part_price'] = f"${cost_info['oem_price']:.2f}"
            repair_item['subtotal'] = f"${cost_info['subtotal']:.2f}"
        else:
            repair_item['oem_part_price'] = 'N/A' if action == 'repair' else 'Data unavailable'
            repair_item['subtotal'] = f"${cost_info['subtotal']:.2f}"
        
        repair_item['total_with_tax'] = f"${cost_info['total_with_tax']:.2f}"
        
        if not cost_info['has_oem_data'] and action == 'replace':
            repair_item['note'] = 'OEM price not available - labor only estimate'
        
        repair_estimate.append(repair_item)
        total_cost += cost_info['total_with_tax']
    
    # STEP 6: Return complete estimate
    return {
        'vehicle': {
            'vin': vin,
            'year': vehicle_info['year'],
            'make': vehicle_info['make'],
            'model': vehicle_info['model']
        },
        'repair_items': repair_estimate,
        'summary': {
            'total_parts': len(consolidated_parts),
            'parts_to_replace': len([r for r in repair_estimate if r['action'] == 'Replace']),
            'parts_to_repair': len([r for r in repair_estimate if r['action'] == 'Repair']),
            'total_estimate': f"${total_cost:.2f}"
        },
        'notes': [
            'Estimate includes 6% sales tax',
            'Labor rate: $55/hour',
            'Based on OEM parts pricing where available',
            'Actual costs may vary based on shop rates and part availability',
            'Multiple images processed and consolidated'
        ]
    }


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    # Example (you'll need to load actual models)
    """
    from PIL import Image
    
    # Load images
    images = [
        np.array(Image.open('damage_1.jpg')),
        np.array(Image.open('damage_2.jpg'))
    ]
    
    # Load trained models (pseudocode)
    part_model = load_model('part_identification_model.h5')
    damage_model = load_model('damage_classification_model.h5')
    
    # Get estimate
    vin = "1HGBH41JXMN109186"
    estimate = estimate_repair_cost(vin, images, part_model, damage_model)
    
    # Print results
    import json
    print(json.dumps(estimate, indent=2))
    """
    
    print("Cost estimation pipeline module loaded.")
    print("Import and use estimate_repair_cost() function with your trained models.")
