# Car Damage Cost Estimator - Complete Workflow

## Project Overview
A machine learning-powered webapp for autobody workers to estimate repair costs by:
1. Decoding vehicle VIN
2. Analyzing damage images
3. Determining repair vs replacement for each part
4. Calculating accurate cost estimates with labor

---

## System Architecture

### **Input**
- VIN (17 characters)
- Images of damaged car (1+ photos from different angles)

### **Output**
- Complete repair estimate with breakdown:
  - Which parts are damaged
  - Repair vs replace decision for each part
  - OEM part prices
  - Labor hours and costs
  - Total estimate with tax

---

## Data Assets

### 1. **VIN Dataset** (848,433 records)
- Purpose: Decode VIN to identify vehicle make/model/year
- Columns: VIN, Make, Model, Year, (possibly Body Style)

### 2. **OEM Parts Database** (39,786+ parts, 27 makes)
- Purpose: Lookup OEM part prices for specific vehicles
- Source: Scraped from oempartsonline.com and toyotapartsdeal.com
- Coverage: Well-covered makes (1000+ parts): 11 makes including Chevrolet, Buick, Cadillac, Acura
- Growing: Toyota comprehensive scraper currently running (457 pages)

### 3. **Car Parts Image Dataset** (998 images, 21 classes)
- Purpose: Train part identification model
- Source: Kaggle dataset
- Classes: Front-bumper, Back-bumper, Hood, Front-door, Back-door, Trunk, Fender, Quarter-panel, Rocker-panel, Running-board, Headlamp, Tail-lamp, Front-windshield, Back-windshield, Front-sideview-mirror, Wheel, Roof, Grille, Door-handle, Fog-lamp, License-plate

### 4. **Damage Classification Dataset** (814 images, 8 classes)
- Purpose: Train damage severity assessment model
- Source: Kaggle dataset
- Classes: Dent, Scratch, Crack, Glass shatter, Lamp broken, Tear, Broken, Missing

### 5. **Labor Hours Reference** (21 parts)
- Purpose: Calculate labor costs for repair vs replacement
- Columns: Part, Repair_Hours, Replace_Hours
- Examples: Front-bumper (3.0h repair, 4.5h replace), Hood (2.0h repair, 3.5h replace)

---

## Machine Learning Models

### **Model 1: Part Identification**
- **Type**: Multi-label CNN classification
- **Architecture**: Transfer learning (ResNet50/EfficientNet with ImageNet weights)
- **Input**: 224×224 RGB image
- **Output**: Probabilities for 21 part classes
- **Training Data**: 998 images
- **Key Feature**: VIN-guided filtering - only considers parts available for specific vehicle

### **Model 2: Damage Severity Assessment**
- **Type**: Multi-label CNN classification
- **Architecture**: Transfer learning (EfficientNetB3 recommended)
- **Input**: 224×224 RGB image (same image as Model 1)
- **Output**: Probabilities for 8 damage types
- **Training Data**: 814 images
- **Key Feature**: Determines repair vs replace decision

---

## Complete Pipeline

```
┌─────────────┐
│  User Input │
│  - VIN      │
│  - Images   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────┐
│ STEP 1: VIN Decoding            │
│ - Query VIN dataset             │
│ - Extract: Make, Model, Year    │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ STEP 2: Vehicle Part Filtering  │
│ - Query OEM database by make    │
│ - Get available part types      │
│ - Map to ML classes (21 → N)    │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ STEP 3: Image Analysis           │
│ For each image:                  │
│  A) Part Identification Model    │
│     → Detect which parts visible │
│  B) Damage Classification Model  │
│     → Assess damage severity     │
│  C) Determine: Repair or Replace │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ STEP 4: Multi-Image Consolidation│
│ - Merge detections across images│
│ - Take highest confidence        │
│ - Keep worst damage (replace>repair)│
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ STEP 5: Cost Calculation         │
│ For each damaged part:           │
│                                  │
│ IF REPLACE:                      │
│  - Query OEM price               │
│  - Get replacement labor hours   │
│  - Cost = (OEM + 55×hours) × 1.06│
│                                  │
│ IF REPAIR:                       │
│  - Get repair labor hours        │
│  - Cost = (55 × hours) × 1.06    │
│                                  │
│ Sum all parts → Total Estimate   │
└──────┬──────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ Output: Complete Estimate        │
│ - Vehicle info                   │
│ - List of damaged parts          │
│ - Repair vs replace for each     │
│ - Cost breakdown                 │
│ - Total with tax                 │
└──────────────────────────────────┘
```

---

## Cost Calculation Formulas

### **Replacement Cost**
```
Cost = (OEM_price + Labor_rate × Labor_hours_replacement) × Sales_tax
Cost = (OEM_price + $55 × hours) × 1.06
```

**Example**: Front bumper replacement
- OEM Price: $450
- Labor Hours: 4.5h
- Calculation: ($450 + $55 × 4.5) × 1.06 = ($450 + $247.50) × 1.06 = $739.35

### **Repair Cost**
```
Cost = Labor_rate × Labor_hours_repair × Sales_tax
Cost = $55 × hours × 1.06
```

**Example**: Hood dent repair
- Labor Hours: 2.0h
- Calculation: $55 × 2.0 × 1.06 = $116.60

### **Mixed Scenario**
If one image shows:
- Front bumper: Broken → REPLACE → $739.35
- Hood: Dent → REPAIR → $116.60
- **Total: $855.95**

---

## Damage Type → Action Mapping

| Damage Type | Action | Reasoning |
|------------|--------|-----------|
| Scratch | **Repair** | Surface damage, can be buffed/painted |
| Dent | **Repair** | Can be pulled, filled, repainted |
| Crack | **Replace** | Structural integrity compromised |
| Glass shatter | **Replace** | Glass cannot be repaired |
| Lamp broken | **Replace** | Sealed electrical component |
| Tear | **Replace** | Material torn, cannot be repaired |
| Broken | **Replace** | Structural failure |
| Missing | **Replace** | Obviously needs replacement |

**Decision Logic**: If ANY damage type requires replacement, the part is replaced.

---

## Implementation Timeline

### **Phase 1: Data Preparation** (Week 1)
- ✅ VIN dataset loaded
- ✅ OEM parts database complete (39,786+ parts)
- ✅ Labor hours reference prepared
- ⏳ Toyota scraper running (comprehensive coverage)
- 🔄 Kaggle dataset downloaded and structured

### **Phase 2: Model 1 - Part Identification** (Week 2-3)
- [ ] Data preprocessing and augmentation
- [ ] Train baseline CNN (transfer learning)
- [ ] Implement VIN-guided filtering
- [ ] Evaluate and optimize (target: >85% accuracy)

### **Phase 3: Model 2 - Damage Assessment** (Week 3-4)
- [ ] Data preprocessing
- [ ] Train damage classification CNN
- [ ] Implement repair/replace logic
- [ ] Validate decision accuracy

### **Phase 4: Integration** (Week 5)
- [ ] Build complete pipeline (cost_estimation_pipeline.py)
- [ ] Test end-to-end workflow
- [ ] Handle edge cases
- [ ] Optimize performance

### **Phase 5: Deployment** (Week 6)
- [ ] Build web interface (Flask/FastAPI)
- [ ] Model optimization (TensorFlow Lite)
- [ ] User testing with autobody workers
- [ ] Refinement based on feedback

---

## Key Design Decisions

### **Why VIN-Guided Filtering?**
- Not all 21 part classes apply to every vehicle
- Reduces false positives (e.g., detecting running boards on a sedan)
- Improves accuracy by constraining search space
- Ensures we only show parts that exist in OEM database

### **Why Multi-Label Classification?**
- Damage images often show multiple parts
- Example: Front corner damage shows bumper + fender + headlight
- Model outputs probability for each class independently
- Threshold at 0.70 for part detection, 0.60 for damage

### **Why Consolidate Multi-Image Detections?**
- Users upload multiple angles of same damage
- Prevents duplicate parts in estimate
- Takes highest confidence and worst damage
- Provides more robust assessment

### **Why Two Separate Models?**
- Part identification and damage assessment are distinct tasks
- Different training data (998 vs 814 images)
- Can update/retrain independently
- Clearer separation of concerns

---

## Technical Stack

### **Backend**
- Python 3.12
- TensorFlow/Keras for deep learning
- Pandas for data manipulation
- NumPy for numerical operations
- Requests + BeautifulSoup for web scraping

### **Models**
- Transfer learning: ResNet50, EfficientNet
- Image size: 224×224 or 299×299
- Optimizer: Adam with learning rate decay
- Loss: Binary cross-entropy (multi-label)

### **Deployment**
- Flask or FastAPI for web API
- TensorFlow Lite for model optimization
- Target inference time: <1 second per image

---

## Files Structure

```
car-damage-cost-estimator/
├── datasets/
│   ├── vin_dataset.csv              (848,433 vehicles)
│   ├── oem_parts_data.csv           (39,786+ parts)
│   ├── labor_hours.csv              (21 parts)
│   └── kaggle/                      (1,812 images)
│       ├── car_parts/               (998 images, 21 classes)
│       └── damage_classification/   (814 images, 8 classes)
│
├── models/
│   ├── part_identification_model.h5
│   ├── damage_classification_model.h5
│   └── training_scripts/
│       ├── train_part_model.py
│       └── train_damage_model.py
│
├── pipeline/
│   ├── cost_estimation_pipeline.py  (Complete integration)
│   ├── vin_decoder.py
│   ├── part_detector.py
│   └── damage_assessor.py
│
├── webapp/
│   ├── app.py                       (Flask/FastAPI)
│   ├── templates/
│   └── static/
│
└── scraping/
    ├── webscraper.py                (Original OEM scraper)
    ├── toyota_json_scraper.py       (Toyota comprehensive)
    └── database_status.py           (Coverage analysis)
```

---

## Next Steps

1. **Immediate**: Wait for Toyota scraper to complete (currently at page 4/457)
2. **Then**: Explore Kaggle dataset structure and prepare training data
3. **Start**: Build training pipeline for Part Identification Model
4. **Follow**: Train Damage Classification Model
5. **Integrate**: Connect all components in cost_estimation_pipeline.py
6. **Deploy**: Build web interface for autobody workers

---

## Success Metrics

### **Model Performance**
- Part Identification: >85% F1-score
- Damage Classification: >80% F1-score
- End-to-end pipeline: <2 seconds per estimate

### **Business Impact**
- Estimate accuracy: Within 20% of actual repair costs
- User satisfaction: >80% find estimates helpful
- Coverage: Support for top 15 vehicle makes in US

---

## Questions Answered

✅ **Do we need damage severity model?** YES - determines repair vs replace
✅ **How to handle multiple images?** Consolidate detections, take worst damage
✅ **How to calculate costs?** Different formulas for repair vs replace
✅ **What about labor?** Included via labor_hours.csv reference
✅ **VIN decoding approach?** Use existing VIN dataset, no external API needed
✅ **Part filtering strategy?** Query OEM database first, constrain ML model
✅ **Sales tax?** 6% applied to all estimates

---

*This workflow is implemented in `cost_estimation_pipeline.py`*
