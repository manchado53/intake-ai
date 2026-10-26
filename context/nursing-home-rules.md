# Nursing-home rules and practice for meal intake (US) — context for Intake.ai

Researched 2026-10-25. Primary sources: 42 CFR 483 (read through the Cornell LII mirror because eCFR blocks bots), CMS SOM Appendix PP (**Rev. 225, 08-08-24**, the PDF CMS currently posts), the CMS MDS 3.0 RAI Manual **v1.20.11 (Oct 2026)**, and the CMS Five-Star Technical Users' Guide (**Sept 2026**).
Labels: "(unverified)" means I could not confirm it from a primary source. "(practice)" means common industry custom, not a rule.

## TL;DR (10 lines)
1. No federal rule requires per-meal "% eaten" charting. What is required: the facility must assess, care-plan, **monitor** and adjust nutrition ([F692](#1-federal-requirements)). Surveyors check monitoring by reviewing "weight records, meal monitors, intake and output logs" ([App. PP F692](https://www.cms.gov/medicare/provider-enrollment-and-certification/guidanceforlawsandregulations/downloads/appendix-pp-state-operations-manual.pdf)).
2. Weight is the federal trigger. Unplanned loss of **5%/1 mo, 7.5%/3 mo, or 10%/6 mo** is "significant" (F692 guidance). MDS item K0300 uses **5%/30 d or 10%/180 d** ([RAI manual](https://www.cms.gov/files/document/final-mds-3-0-rai-manual-v1-20-11-october-2026.pdf)).
3. Weight is a lagging signal. Intake is the leading signal. CMS says weight loss "should be considered avoidable" unless the facility shows it assessed, intervened, **monitored**, and coordinated care (F692).
4. Today's CNA charting is poor. Staff **overestimate intake by about 20–22%**. They miss **more than half** of residents eating ≤75% ([Simmons 2000](https://pubmed.ncbi.nlm.nih.gov/10682952/), [Pokrywka 1997](https://pubmed.ncbi.nlm.nih.gov/9329485/)). Whole-tray quartile estimates were correct only **44%** of the time ([Castellanos 2002](https://pubmed.ncbi.nlm.nih.gov/12067049/)).
5. Before/after **tray photos matched direct observation** ([Simmons 2000](https://pubmed.ncbi.nlm.nih.gov/10682952/)). RGB-D (color plus depth) intake estimation has been shown in LTC (long-term care) plate datasets ([Pfisterer 2022](https://pubmed.ncbi.nlm.nih.gov/34997022/)). This is the evidence base for Intake.ai.
6. Malnutrition in nursing homes / LTC: **17.5% / 28.7%** malnourished by MNA (meta-analysis, [Cereda 2016](https://pubmed.ncbi.nlm.nih.gov/27086194/)). Dehydration: **20%** of care-home residents ([Hooper 2016](https://pubmed.ncbi.nlm.nih.gov/26553658/)).
7. Protein target for older adults: **1.0–1.2 g/kg/day**, and **1.2–1.5 g/kg/day** when ill ([PROT-AGE](https://pubmed.ncbi.nlm.nih.gov/23867520/)). Malnutrition criteria use intake **<75% of estimated energy need for ≥1 month** (chronic illness) ([AND/ASPEN 2012](https://pubmed.ncbi.nlm.nih.gov/22535923/)).
8. Money: weight loss is **not** one of the Five-Star quality-measure ratings. Pressure ulcers are ([Five-Star guide](https://www.cms.gov/medicare/provider-enrollment-and-certification/certificationandcomplianc/downloads/usersguide.pdf)). Survey deficiencies (F692 harm = G-level, 20+ points) hit the Five-Star inspection rating and can bring CMPs (civil money penalties) of up to about $27k per day or per instance ([2025 CMS CMP table](https://www.cms.gov/files/document/ltc-hha-hospice-clia-calculations-cmp-adjustments-2025.pdf)).
9. Privacy: CMS lists photographing "a resident eating in the dining room" without **written consent** as a privacy violation ([F583](https://www.cms.gov/medicare/provider-enrollment-and-certification/guidanceforlawsandregulations/downloads/appendix-pp-state-operations-manual.pdf)). So the camera should see **plates only, at the dish-return station**. Tray tickets carry names, so images are PHI (protected health information). Full-face images are a HIPAA identifier ([45 CFR 164.514](https://www.law.cornell.edu/cfr/text/45/164.514)).
10. Position Intake.ai as **documentation plus decision support for the RD/DON**: it flags, and humans decide. Do not claim it diagnoses malnutrition. Any FDA device question needs counsel (see §7).

---

## 1. Federal requirements

| Tag | Reg | What it requires | What surveyors look for / common deficiency |
|---|---|---|---|
| **F692** Nutrition/hydration | [483.25(g)(1)-(3)](https://www.law.cornell.edu/cfr/text/42/483.25) | Keep "acceptable parameters of nutritional status, such as usual body weight or desirable body weight range". Offer enough fluid. Offer a therapeutic diet when there is a nutritional problem. | Failure to "accurately and consistently assess"; to "identify, implement, monitor, and modify interventions"; to notify the physician; to provide an ordered therapeutic diet. **Level 3 (harm) example: "failure to identify a decrease in food intake, which resulted in a significant, unintended weight loss."** ([App. PP F692](https://www.cms.gov/medicare/provider-enrollment-and-certification/guidanceforlawsandregulations/downloads/appendix-pp-state-operations-manual.pdf)) |
| **F693** Tube feeding | 483.25(g)(4)-(5) | Do not tube-feed a resident who can eat orally unless it is clinically indicated and consented. Restore oral skills if possible. Prevent complications (aspiration, diarrhea, dehydration…). | Enteral orders, complication prevention. Out of scope for a plate camera. |
| **F800** Food & nutrition (general) | [483.60](https://www.law.cornell.edu/cfr/text/42/483.60) | "Nourishing, palatable, well-balanced diet" that meets daily needs and takes preferences into account. | Cited for **system-wide** dietary-department failures. |
| **F801** Qualified staff | 483.60(a)(1)-(2) | Employ a qualified dietitian (full-time, part-time, or consultant). If not full-time, designate a director of food & nutrition services (e.g., CDM, certified dietary manager) with frequent RD consults. | Credentials, consultation frequency. |
| **F802** Sufficient staff | 483.60(a)(3) | Enough competent food-service staff for the facility assessment. | Late or cold trays, staffing gaps. |
| **F803** Menus | 483.60(c) | Menus meet nutritional needs "in accordance with established national guidelines". Prepared in advance, **followed**, updated periodically. Reflect religious/cultural needs. **RD-reviewed** for adequacy. | Probe: "Residents are receiving food in the **amount, type, consistency and frequency** to maintain normal body weight." Deviations from the planned menu need documentation. Level 4 example: wrong texture served to a puree-diet resident, leading to choking. Level 1: substitutions not noted on the menu. |
| **F804** Nutritive value / palatability | 483.60(d)(1)-(2) | Cooking preserves nutrients. Food is palatable, attractive, at a safe and appetizing temperature. | Taste tests, temperature checks, resident complaints. |
| **F805** Form of food | 483.60(d)(3) | Food prepared "in a form designed to meet individual needs". | "Is the food cut, chopped, ground, or pureed for individual resident's needs?" |
| **F806** Allergies / preferences / substitutes | 483.60(d)(4)-(5) | Accommodate allergies, intolerances, preferences. Offer "appealing options of similar nutritive value" when a resident refuses a meal. | "If a resident appears to refuse food… determine if he or she is offered… substitutes." |
| **F807** Drinks | 483.60(d)(6) | Water and other drinks sufficient for hydration, matched to preferences. | Fluid access, pass checks. |
| **F808** Therapeutic diets | 483.60(e) | Ordered by a physician or NPP, or delegated to an RD where state law allows. **Texture modifications must be specific in the order.** | Is the diet ordered? Is it delivered as ordered? |
| **F809** Meal frequency / snacks | 483.60(f) | ≥3 meals per day. **≤14 h** from evening meal to breakfast, or **16 h** if a nourishing bedtime snack is served and the resident group agrees. Alternatives at non-traditional times. | Meal schedules, snack availability. |
| **F810** Assistive devices | 483.60(g) | Adaptive utensils plus help using them. | Device in care plan but not on tray. |
| **F811** Paid feeding assistants | 483.60(h) | State-approved training. Supervised by an RN/LPN. Only for residents without complicated feeding problems. | Training records, resident selection. |
| **F812** Food safety | 483.60(i)(1)-(2) | Approved sources. Store/prepare/serve per professional food-safety standards. | Most-cited dietary tag in practice (unverified count). Temps, labeling, hand hygiene, reheating puree. |
| **F813** Outside food | 483.60(i)(3) | Policy on food brought by family/visitors. | Policy exists and is followed. **Note:** outside food is invisible to a tray camera. |
| **F814** Refuse | 483.60(i)(4) | Dispose of garbage properly. | n/a |
| **F636** Comprehensive assessment | [483.20(b)](https://www.law.cornell.edu/cfr/text/42/483.20) | RAI/MDS assessment, including nutritional status. Admission, then quarterly/annual and on significant change. | Is the MDS accurate? (Section K coded right?) |
| **F656** Comprehensive care plan | [483.21(b)](https://www.law.cornell.edu/cfr/text/42/483.21) | Person-centered plan with **"measurable objectives and timeframes"**. | Is the care plan **implemented**? F692 guidance says the nutrition plan must give "a time frame and parameters for monitoring". |

Key F692 guidance quotes ([App. PP](https://www.cms.gov/medicare/provider-enrollment-and-certification/guidanceforlawsandregulations/downloads/appendix-pp-state-operations-manual.pdf)):
- "Weight loss, poor nutritional status, or dehydration should be considered avoidable unless the facility can prove it has assessed/reassessed… consistently implemented… **monitored for effectiveness**."
- "Poor intake… or a change in the resident's usual intake that **persists for multiple meals**, may indicate an underlying condition or illness."
- Weigh on admission, **weekly for the first 4 weeks**, then **at least monthly**. Also weigh when "food intake has declined and persisted (e.g., for more than a week)."
- The nutrition assessment includes "an estimate of calorie, nutrient and fluid needs, and **whether intake is adequate** to meet those needs."
- "Intake alone is not the only factor that can affect nutritional status." Weight loss alone is not enough to cite F692, and its absence does not prove compliance.
- Level 4 (IJ, immediate jeopardy) example: downgraded textures (mechanical soft/pureed) against resident preference led to a decline in intake and severe weight loss. **Texture changes cut intake.**

Real-world examples (CMS-2567 surveys via a third-party aggregator; examples only):
- [Shafter Nursing Care, CA, 2021](https://readyrule.com/nursing-home/120000375-shafter-nursing-care/report/2021-04-07): 20 lb (11.8%) loss in a month was not reported to the physician. Dietary notes showed meal intake around 0–25%. The RD's fortified-diet recommendation was not carried out.
- [Alden Park Strathmoor, 2026](https://readyrule.com/nursing-home/145259-alden-park-strathmoor/report/2026-01-21): actual-harm F692. The RD and physician were not notified of significant weight loss. No intervention for 5 days.
- [Avenue at Wooster, OH, 2024](https://readyrule.com/nursing-home/366463-avenue-at-wooster/report/2024-05-23): the RD's recommendation was never passed to the prescriber. Each discipline assumed another had acted.
- Pattern: the failure is usually **communication/escalation**, not missing data. This is where an alert loop adds value.

## 2. Intake documentation: required vs customary

| Item | Status | Source |
|---|---|---|
| Per-meal % intake charting | **Not federally mandated.** Customary. Usually a facility policy or care-plan intervention ("monitor meal intake"). Surveyors review "meal monitors" as evidence of monitoring. | [App. PP F692](https://www.cms.gov/medicare/provider-enrollment-and-certification/guidanceforlawsandregulations/downloads/appendix-pp-state-operations-manual.pdf) |
| Scale | Whole-tray **0/25/50/75/100%** is the common method | [Castellanos 2002](https://pubmed.ncbi.nlm.nih.gov/12067049/) |
| Who charts | **CNAs** (certified nursing assistants), usually in the EHR's point-of-care/kiosk module after the meal (practice) | [Castellanos 2002](https://pubmed.ncbi.nlm.nih.gov/12067049/); EHR detail (unverified) |
| "Low intake" definition | Research and old MDS 2.0 (item K4c "leaves 25% or more of food uneaten at most meals"): **<75% of most meals** | [Simmons 2002](https://scholars.mssm.edu/en/publications/accuracy-of-minimum-data-set-in-identifying-residents-at-risk-for-2/), [Simmons 2000](https://pubmed.ncbi.nlm.nih.gov/10682952/) |
| Facility RD-referral triggers | Typical: **<50% for 3 consecutive meals**, or **<75% average over ~7 days**, or any meal refusal streak (practice, **unverified**; varies by facility policy) | [teaching material](https://www.cas.miamioh.edu/bridgeproject/Nutrition_Course_1.pdf) cites <75% (MDS) and <50% (clinically significant) |
| Weight triggers | F692: 5%/1 mo, 7.5%/3 mo, 10%/6 mo. MDS K0300: ≥5%/30 d or ≥10%/180 d. K0300 codes 0 = no, 1 = yes on a prescribed weight-loss regimen, 2 = yes not on a regimen. | [App. PP](https://www.cms.gov/medicare/provider-enrollment-and-certification/guidanceforlawsandregulations/downloads/appendix-pp-state-operations-manual.pdf), [RAI K-4](https://www.cms.gov/files/document/final-mds-3-0-rai-manual-v1-20-11-october-2026.pdf) |
| Weight formula | % loss = (usual − actual) / usual × 100 | F692 guidance |
| MDS nutrition items | K0100 swallowing signs. K0200 height/weight. K0300/K0310 loss/gain. **K0520** nutritional approaches (A parenteral/IV, B feeding tube, C mechanically altered diet, D therapeutic diet). K0710 % calories/fluid by tube. | [RAI manual Ch. 3 §K](https://www.cms.gov/files/document/final-mds-3-0-rai-manual-v1-20-11-october-2026.pdf) |

How intake ties to the care plan:
```
admission -> MDS + RD nutrition assessment (est. kcal/protein/fluid need)
          -> care plan: goal (target weight range, fluid goal) + interventions
             (supplement, fortified foods, assist level, texture) + monitoring parameters
          -> daily: CNA meal % charting, weights weekly x4 then monthly
          -> trigger (intake streak / weight loss) -> RD review -> MD/NP notified
          -> care plan revised -> loop
```
K0300 guidance: weight loss must be "assessed and care planned at the time of detection and not delayed until the next MDS assessment" ([RAI K-4](https://www.cms.gov/files/document/final-mds-3-0-rai-manual-v1-20-11-october-2026.pdf)).

## 3. Accuracy problems, staff time, prevalence

| Finding | Number | Source |
|---|---|---|
| Staff vs weighed trays (27 residents, 3 NHs) | Off by **~20%**, mostly **overestimated**. **~1/3** of at-risk residents missed. Chart often matched neither actual intake nor the staff's own estimate. | [Pokrywka 1997, JAGS](https://pubmed.ncbi.nlm.nih.gov/9329485/) |
| Staff charting vs observation vs photos (56 residents, 9 meals each) | Staff **overestimated by 22%**. Missed **53%** of residents eating ≤75% at most meals. **Photo method = direct observation.** | [Simmons & Reuben 2000, JAGS](https://pubmed.ncbi.nlm.nih.gov/10682952/) |
| Whole-tray 0–100% quartile method (42 residents, 109 meals) | ICC **0.464**. Correct **44%** of the time. Still 38–44% correct with no distractions. "Not sufficiently accurate to identify residents who are eating less than 75%." | [Castellanos & Andrews 2002, JADA](https://pubmed.ncbi.nlm.nih.gov/12067049/) |
| MDS under-identifies risk (75 residents) | Low intake (<75%) found by researchers in **73%** vs **44%** on the MDS | [Simmons, Lim, Schnelle 2002, JAMDA](https://scholars.mssm.edu/en/publications/accuracy-of-minimum-data-set-in-identifying-residents-at-risk-for-2/) |
| Staff time, feeding assistance | **35–40 min of staff time per resident per meal** to give assistance that improves intake | [Simmons & Schnelle 2006, JAGS](https://pubmed.ncbi.nlm.nih.gov/16776786/) |
| Staff time, intake charting itself | No good published number found (**unverified**) | — |
| Malnutrition, MNA meta-analysis | Nursing homes **17.5%**, long-term care **28.7%**, rehab/sub-acute **29.4%** | [Cereda 2016, Clin Nutr](https://pubmed.ncbi.nlm.nih.gov/27086194/) |
| Malnutrition, pooled MNA (n = 4,507) | Nursing home **13.8%** malnourished. About 2/3 of all subjects malnourished or at risk. | [Kaiser 2010, JAGS](https://pubmed.ncbi.nlm.nih.gov/20863332/) |
| Malnutrition (LTC, cited) | "54% of older adults in LTC" | [Pfisterer 2022](https://pubmed.ncbi.nlm.nih.gov/34997022/) (secondary citation) |
| Dehydration (UK care homes, n = 188) | **20%** (serum osmolality >300 mOsm/kg). **Thirst did not predict it.** | [Hooper 2016, J Gerontol A](https://pubmed.ncbi.nlm.nih.gov/26553658/) |
| Automated RGB-D intake (LTC plates) | Depth-refined segmentation. Mean intake error well below the typical human error. Flags "visual-volume discordance": area ≠ volume. | [Pfisterer 2022, Sci Rep](https://pubmed.ncbi.nlm.nih.gov/34997022/) |

Why staff charting fails: too many tasks at mealtime, vague estimation rules, charting delayed, little supervision ([Castellanos 2002](https://pubmed.ncbi.nlm.nih.gov/12067049/); [VUMC summary](https://vumc.org/cqa/node/96)).

## 4. Menus, portions, diets, nutrient data

- **Cycle menus**: menus written ahead and repeated on a cycle (often 3–5 weeks), RD-reviewed for adequacy ([483.60(c)](https://www.law.cornell.edu/cfr/text/42/483.60)). The cycle length is practice (unverified). CMS warns of "menu fatigue" and cites repetitive menus at Level 2 ([F803](https://www.cms.gov/medicare/provider-enrollment-and-certification/guidanceforlawsandregulations/downloads/appendix-pp-state-operations-manual.pdf)).
- **Standardized recipes and portion control**: portions are served with numbered scoops (dishers). Scoop number = scoops per quart: **#8 = ½ cup, #12 = ⅓ cup, #16 = ¼ cup** ([USDA Food Buying Guide Table 13](https://foodbuyingguide.fns.usda.gov/Content/TablesFBG/Table13_FBG_Sizes_and_Capacities_of_Scoop_s_(or_Dishers).pdf)). Scoops measure volume, not weight ([CBORD poster](https://impacweb.cbord.com/reportsets/~common/Common%20Measurements%20Poster.pdf)). **Design hook:** the "before" portion is roughly known from the menu's scoop size.
- **Therapeutic diets** (F808): physician- or RD-ordered, e.g., sodium-restricted, carb-consistent, renal, gluten-free. Texture must be specific in the order.
- **Texture-modified diets**: legacy US terms are "mechanical soft", "ground", "pureed". **IDDSI** (International Dysphagia Diet Standardisation Initiative) levels: drinks 0 thin to 4 extremely thick; foods 3 liquidised, 4 pureed, 5 minced & moist, 6 soft & bite-sized, 7 regular / easy-to-chew ([Cichero 2017](https://pubmed.ncbi.nlm.nih.gov/27913916/)). CMS does not mandate IDDSI. Many vendors support it ([MatrixCare MealTracker](https://intuitionlabs.ai/software/pdfs/matrixcare-mealtracker.pdf), vendor claim). **CV impact:** purees and minced foods have no item shape, so the model must segment by color/region and use depth.
- **Substitutions**: residents may refuse and get an alternative "of similar nutritive value" (F806). Substitutions should be noted (F803 Level 1). **Design hook:** the tray ticket says what *should* be there. The camera must handle "served item ≠ ticket item".
- **Per-portion nutrient data**: comes from dietary/menu software with standardized recipes and nutrient analysis. Vendor examples: [GFS Cycle Menu Management](https://experience.gfs.com/resources/healthcare-senior-living/healthcare-menu-technology/cycle-menu-management) (prints tray tickets/cards), [MatrixCare MealTracker](https://intuitionlabs.ai/software/pdfs/matrixcare-mealtracker.pdf) (USDA FoodData Central analysis, HL7 diet orders from the EHR), [DiningManager](https://www.capterra.ca/software/218235/diningmanager) (tray tickets, PCC/MatrixCare integrations). MealSuite, CBORD, and Computrition are also common in healthcare (unverified for LTC share). The tray ticket comes from this software and lists resident, room, diet, texture, allergies, likes/dislikes, and items (practice).
- **Protein needs**: PROT-AGE says **≥1.0–1.2 g/kg/day** for healthy people over 65, **1.2–1.5** with acute/chronic disease, and limits for eGFR <30 not on dialysis ([Bauer 2013](https://pubmed.ncbi.nlm.nih.gov/23867520/)). The ESPEN geriatrics guideline gives about 30 kcal/kg/day energy and ≥1 g/kg/day protein ([Volkert 2019](https://pubmed.ncbi.nlm.nih.gov/30005900/); numbers from full text, **unverified** here). Example: 60 kg resident → 60–72 g protein/day → about 20–24 g per meal.

## 5. Quality measures and money

**Five-Star** ([Technical Users' Guide, Sept 2026](https://www.cms.gov/medicare/provider-enrollment-and-certification/certificationandcomplianc/downloads/usersguide.pdf)):
- Three domains: health inspections, staffing, QMs (quality measures).
- Long-stay MDS QMs used in the rating: ADL decline, walking decline, **pressure ulcers** (replaced "high-risk pressure ulcers" in Jan 2025), catheter, UTI, falls with major injury, antipsychotics. Short-stay: discharge function, **new/worsened pressure ulcers**, new antipsychotics. Plus claims-based hospitalizations and ED visits.
- **Weight loss is not in the Five-Star QM rating.** CMS still publishes a long-stay "lose too much weight" MDS measure through the Nursing Home Quality Initiative / Care Compare. Exact current spec is **unverified**; see the [QM User's Manual](https://www.cms.gov/medicare/quality-initiatives-patient-assessment-instruments/nursinghomequalityinits).
- Nutrition still matters to the rating indirectly: malnutrition drives pressure ulcers, falls, and hospitalizations (clinical link, not a CMS formula).
- Inspection scoring: deficiency points by scope/severity. D/E/F = 4/8/16. **G/H/I (actual harm) = 20/35/45.** J/K/L (IJ) = 50/100/150 (guide Table 1). One F692 harm citation (G) outweighs several D-level food-safety tags.

**Civil money penalties** ([42 CFR 488.438](https://www.law.cornell.edu/cfr/text/42/488.438); [CMS 2025 inflation table](https://www.cms.gov/files/document/ltc-hha-hospice-clia-calculations-cmp-adjustments-2025.pdf)):

| Type | Base reg range | 2025 adjusted |
|---|---|---|
| Per day, IJ | $3,050–$10,000 | ~$8,351–$27,378 |
| Per day, non-IJ | $50–$3,000 | ~$136–$8,211 |
| Per instance | $1,000–$10,000 | ~$2,739–$27,378 |

The 2025 figures come from my reading of the CMS worksheet columns. Verify them before quoting.

**PDPM** (Medicare Part A SNF payment) nutrition hooks ([RAI manual Ch. 6](https://www.cms.gov/files/document/final-mds-3-0-rai-manual-v1-20-11-october-2026.pdf)):
- **SLP component**: uses a mechanically altered diet (K0520C) or a swallowing disorder (K0100).
- **NTA component**: **Malnutrition** diagnosis (I8000) = 1 point. Feeding tube while a resident = 1 point. Parenteral/IV feeding is scored high or low intensity.
- **Nursing component, Special Care High**: includes fever plus **weight loss (K0300 = 1 or 2)**.
- Takeaway: accurate documentation of malnutrition and weight loss affects payment. Intake data supports that documentation; it is not a billing tool by itself.

**Who owns it** (roles from regs where noted; buying process is practice/unverified):

| Role | Owns | Likely stance on Intake.ai |
|---|---|---|
| Administrator (NHA) | Whole facility, survey results, budget ([483.70](https://www.law.cornell.edu/cfr/text/42/483.70)) | **Economic buyer** for a single facility. Multi-facility chains often decide at regional/corporate level, through clinical ops + IT (unverified). |
| DON (director of nursing, RN) | CNAs, charting, care-plan execution, weights ([483.35](https://www.law.cornell.edu/cfr/text/42/483.35)) | **Key approver.** Wants less CNA charting burden and fewer missed declines. |
| RD (often a part-time consultant) | Nutrition assessment, menu review, recommendations (483.60(a)) | **Primary daily user** of alerts and trends. |
| Dietary Manager / CDM | Kitchen, menus, tray tickets, portions | Owns the dish-return station and menu data feed. |
| CNAs | Serve trays, assist, chart % intake | Must not get extra steps. Tray scan has to be ~zero-touch. |
| MDS coordinator | Section K accuracy | Wants weights and intake history. |
| Compliance / Privacy Officer, IT | HIPAA, BAAs, network | Gatekeepers. |

## 6. Privacy and security

| Issue | Rule / fact | Source |
|---|---|---|
| Photographing residents | Photos/recordings of a resident without the resident's or representative's **written consent** violate privacy. CMS's own example: "a resident eating in the dining room". | [App. PP F583 (483.10(h))](https://www.cms.gov/medicare/provider-enrollment-and-certification/guidanceforlawsandregulations/downloads/appendix-pp-state-operations-manual.pdf) |
| Dignity while dining | Avoid daily disposable dishware, bibs (unless the resident chooses), staff standing over residents | [App. PP F550](https://www.cms.gov/medicare/provider-enrollment-and-certification/guidanceforlawsandregulations/downloads/appendix-pp-state-operations-manual.pdf) |
| Abuse via images | Demeaning photos or social-media posts are cited as abuse (F600 area) | App. PP |
| Clinical photos allowed | Wound photos are OK "if the facility has developed a protocol… and issues related to resident privacy and dignity are considered" | App. PP (pressure ulcer guidance) |
| PHI in images | Tray ticket = name + room + diet (health info linked to a person) → PHI. **Full-face photos** are Safe Harbor identifier (Q). Names (A), dates (C), and "any other unique identifying number" (R) also count. | [45 CFR 164.514(b)(2)](https://www.law.cornell.edu/cfr/text/45/164.514) |
| Minimum necessary | Limit PHI use/disclosure to what is needed | [45 CFR 164.514(d)](https://www.law.cornell.edu/cfr/text/45/164.514) |
| Cloud vendors | A cloud provider holding ePHI is a **business associate even without the encryption key**. A BAA (business associate agreement) is required. | [HHS cloud guidance](https://www.hhs.gov/hipaa/for-professionals/special-topics/cloud-computing) |
| Slack alerts | Slack, Roboflow hosted inference, and any LLM API all need a BAA before touching PHI. Many tiers do not offer one (check each vendor; **unverified** per vendor). | HHS cloud guidance |

Practical rules:
```
camera FOV  -> plate + ticket only, at dish return. No dining-room cameras.
on device   -> decode QR -> swap name for opaque resident_id -> mask/crop ticket text
            -> blur any face/hand region (defense in depth)
store       -> plate crops + resident_id + timestamps; images expire (e.g., 30-90 d, TBD)
send out    -> alerts carry resident_id/room initials + link into an authenticated app,
               not name + diagnosis in a Slack channel (unless a BAA covers Slack)
demo        -> synthetic tickets, fake names, no real residents (already the plan)
```

## 7. Design implications (what this means for Intake.ai)

What to measure:
- Per item: **% remaining → % eaten** (0–100, keep the continuous value) plus a **quartile bucket** (0/25/50/75/100) so it maps to existing CNA charting and EHR fields.
- Per meal: **kcal and protein (g) eaten** = Σ item % eaten × menu-portion nutrients. Also fluid (mL) if cups are scanned. Units: kcal, g, mL, %.
- Per day/week: **% of estimated need** (kcal, protein g/kg) = the AND/ASPEN energy-intake criterion's currency.
- Record **confidence** and "not scanned / tray missing / refused / substitution" states. Missing data ≠ 0% eaten.

Thresholds (configurable per facility, with defaults from the literature, not law):
- Low meal: **<50%** of meal (kcal-weighted). Low-intake pattern: **<75% average over 7 days** (MDS-era / AND-ASPEN 75% line).
- Streak alert: **≥3 consecutive low meals** or a refusal streak (facility-policy-style default, **unverified** as standard).
- Protein: day total < (1.0 g/kg × weight) for N days.
- Weight (if entered): flag **5%/30 d, 7.5%/90 d, 10%/180 d** with the F692 formula.
- Fluids: CMS sets no numeric target ("no reliable calculation", F692). Use the RD's care-plan goal.

Alerts and audiences:
- RD + DON get alerts and trend views. Unit nurse/charge nurse gets a same-shift "low intake" heads-up. CNAs get no extra task.
- Every alert needs an **acknowledge → action** record: who saw it, when, what was done (notified MD/NP, supplement started, care plan revised). This closes the escalation gap seen in 2567s.
- Export or write back a meal % field so the EHR stays the system of record (integration TBD).

What NOT to claim:
- Not "diagnoses malnutrition", not "prevents weight loss", not "replaces RD assessment", not "ensures compliance / survey-proof".
- Say: "objective meal-intake documentation and trend alerts to support RD/IDT (interdisciplinary team) decisions."
- FDA (Jan 2026 [CDS guidance](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/clinical-decision-support-software), four non-device CDS criteria under FD&C Act 520(o)(1)(E)): showing intake data plus rule-based flags to clinicians who can review the basis likely sits outside device rules. Criterion 1 excludes software that analyzes **medical images/signals**. A food photo is arguably not a medical image, but this is **unverified** and needs regulatory counsel. Keep outputs transparent (show the before/after images and the math) so a clinician can independently review the basis (criterion 4).

---

## Design rules for Intake.ai (checklist)
- [ ] Camera sees plates/trays only, at dish return. Never the dining room or faces (F583).
- [ ] Faces/hands auto-blurred on device. Tray-ticket text masked after QR decode.
- [ ] QR → opaque `resident_id`. The name→ID map lives only in facility systems.
- [ ] Works with reusable dishware (F550 dignity: no forced disposables or special plates).
- [ ] Per-item % eaten (continuous) + quartile bucket + confidence + reason codes (refused, substituted, not scanned, outside food).
- [ ] Nutrients come from the facility's menu/recipe data (portion = scoop/serving size). Never invented by the model.
- [ ] Handles texture-modified items (IDDSI 4–6, puree). Uses depth for volume, not just mask area.
- [ ] Handles substitutions: served item ≠ ticket item → flag it, don't silently mis-assign nutrients.
- [ ] Daily kcal and protein vs a resident-specific target (RD-entered, default 1.0–1.2 g/kg).
- [ ] Alert rules are configurable. Defaults: meal <50%, 3-meal streak, 7-day avg <75%, protein < target. Optional weight-loss % rules.
- [ ] Alerts go to RD/DON/charge nurse with minimum-necessary content. No names in Slack without a BAA.
- [ ] Every alert has an ack + action + timestamp audit trail. Every manual correction of a % is logged (who/when/old→new).
- [ ] Image retention window is set and enforced. Encrypted at rest/in transit. Role-based access.
- [ ] Missing scans are visible (coverage %). Missing ≠ 0%.
- [ ] Copy says "decision support / documentation aid". No diagnosis or compliance guarantees.
- [ ] Demo uses synthetic residents and tickets only.

## Open questions / uncertain
- Appendix PP: CMS announced 2025 guidance revisions (e.g., to admission/discharge, chemical restraints, nutrition-adjacent tags?). The PDF I parsed is Rev. 225 (Aug 2024). Confirm whether F692/F8xx text changed in 2025–2026 (**unverified**).
- Exact current spec of the long-stay weight-loss QM (NHQI / Care Compare) and whether it is still publicly reported.
- Typical facility RD-referral thresholds (<50% × 3 meals, etc.): a common practice, but I found no authoritative standard. Ask a practicing RD/DON.
- Time CNAs spend charting intake per shift: no solid study found.
- Whether Slack / Roboflow hosted / other vendors sign BAAs on the tiers the demo would use. Check each.
- FDA status of image-derived intake estimates (does a food photo count as a "medical image" under CDS criterion 1?). Needs counsel.
- Whether state rules add intake/weight requirements beyond federal (varies by state, not researched).
- Accuracy target: what % eaten error is "good enough"? Literature suggests beating human charting (~20% error, 44% agreement on quartiles) is the bar. A pilot-specific target is still TBD.
- Exact 2025/2026 CMP amounts (verify against the 45 CFR 102.3 table).
