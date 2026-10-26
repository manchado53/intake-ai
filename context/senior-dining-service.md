# One plate or the whole tray? What the Plate Check camera should target

Researched 2026-10-26. This builds on `context/nursing-home-rules.md` and `market-research.md` and does not repeat them. (Those files cover F692, the 25% charting accuracy studies, IDDSI levels, Meal Vision, Nuvilab, foodintech and AFINI-T at a high level.)
Tags: **[U]** = unverified or weak source. **(practice)** = industry custom, not a rule.

## Answer first

```
 DESIGN the rig for a TRAY-sized view.   TRAIN + DEMO on the MAIN PLATE.
 +-------------------------------+        +-----------+
 | [bowl] [cup]  [dessert]       |        |  (plate)  |  <- v1 model scope
 |      ( MAIN PLATE )   [milk]  |        |  entree   |
 | [ticket QR]                   |        |  starch   |
 +-------------------------------+        |  veg      |
   field of view fits a tray              +-----------+
   (side vessels = v2 classes)
```

- **v1 model and live demo:** one round main plate per shot, seen from above, with 2–4 items on it (protein, starch, vegetable), plus the ticket QR beside it.
- **Camera rig:** frame it to fit a full tray, so side bowls and cups can be added later with no hardware change.
- **v2:** side vessels (soup bowl, dessert dish, milk or supplement carton) as their own detected containers.

Why:
1. Most dining is now plated, not served on trays. CMS treats trays in the dining room as an institutional practice (§1).
2. Staff chart one number per meal, and the entrée counts most in it. The main plate carries most of that signal and most of the protein (§3).
3. Published LTC imaging systems that measure intake per item photograph **one plate at a time**: AFINI-T, Meal Vision, Pouyet. Only Nuvilab Nutri-Guard photographs a whole tray (§5).
4. Trays still exist for residents who eat in their rooms. A tray-sized field of view keeps that path open (§1).

---

## 1. How meals are served

| Evidence | What it says | Source |
|---|---|---|
| CMS surveyor form **CMS-20053 Dining Observation (10/2022)**, F584 "homelike environment" | Lists "**Meals served on trays in a dining room**" as an institutional practice that "may interfere with the quality of the residents' dining experience". Also lists "nondisposable cutlery and dishware" (F550), and "**Wait for residents at a table to finish their meals before scraping food from plates at that table.**" | [CMS-20053 PDF](https://qsep.cms.gov/data/168/CMS-20053Dining.pdf) (text read from the PDF) |
| State plans of correction | Facilities commit to "removing trays from dining room tables" and serving on a placemat. Surveyors cite meals served on trays in dining rooms. | [MI LARA POC](https://val.apps.lara.state.mi.us/Files/ViewDocument/59718), [NC 2567](https://info.ncdhhs.gov/DHSR/facilities/nh/2016/20161207-923206.pdf) |
| FoodService Director 2016 LTC/Senior Living Census (n = 244 operators; multi-select, so shares can add to more than 100%) | Restaurant-style in the dining room **70%** (97% at sites serving 300+ meals a day). Room-service style to bedridden residents **45%**. Non-select tray to bedridden residents **16%** (down from 23% in 2014). Family style **11%**. Buffet **20%**. | [FSD 2016](https://www.foodservicedirector.com/senior-dining-meals/2016-ltc-senior-living-census-how-seniors-modern-tastes-are-changing-menus), [FSD 2014](https://www.foodservicedirector.com/senior-dining-meals/2014-ltc-senior-living-census-ancillary-foodservice-locations-gain-in-popularity) |
| Culture change adoption | 56% of NHs reported some culture change in 2007 and 85% in 2009–10. LeadingAge: **13% full adoption, 74% partial**. | [PMC6177048](https://pmc.ncbi.nlm.nih.gov/articles/PMC6177048), [LeadingAge](https://leadingage.org/leadingage-study-person-centered-care-engages-nursing-home-residents/) |
| Pioneer Network New Dining Practice Standards (2011), adopted in CMS S&C 13-13-NH | Pushes liberalized diets and resident choice. Training material says "move away from tray and pre-plate service". | [CMS S&C 13-13](https://cms.gov/medicare/provider-enrollment-and-certification/surveycertificationgeninfo/policy-and-memos-to-states-and-regions-items/survey-and-cert-letter-13-13), [MO DHSS webinar](https://ltc.health.mo.gov/archives/10973) |
| Contractor examples | HHS Culinary removed tray lines at all 7 of its senior living accounts (AL and SNF), with china in dining rooms. Manchester Manor (CT) dropped tray service. | [FSD](https://www.foodservicedirector.com/senior-dining-meals/hhs-replaces-senior-dining-tray-lines-with-country-kitchen-approach), [Provider 2013](https://www.providermagazine.com/Issues/2013/Pages/1213/Service-And-Savings-Go-Hand-In-Hand.aspx) |
| Household model | Small units (24 residents or fewer) around their own kitchen. Food is plated in the unit kitchenette. AFINI-T was built at Schlegel Villages and notes "food is plated from a centralized location (e.g., in a kitchenette)". | [UWM thesis](https://dc.uwm.edu/etd/1527), [AFINI-T arXiv](https://arxiv.org/pdf/2112.04608) |

Summary:
```
DINING ROOM (most meals)          ROOM (bed-bound, isolation, short-stay rehab)
plated at servery/steam table     tray from tray line or cart
plate set on table, no tray       tray + plate under dome + side bowls + drinks
sides in small dishes on table    everything on one tray
-> plates bussed, then scraped    -> whole tray returned on cart
```
- No national figure was found for the **share of meals** eaten in rooms vs the dining room [U]. The FSD numbers count operators that offer a format, not meals served.
- Assisted living leans even further toward restaurant style, with menus and ordering at the table ([FES](https://fesmag.com/topics/trends/14528-senior-living-foodservice-gets-an-upgrade), [SNN 2017](https://skillednursingnews.com/2017/08/restaurant-style-dining-among-hot-food-trends-skilled-nursing/)).
- Short-stay rehab SNF residents eat in their rooms more often (practice, [U]).
- **Camera-placement catch:** CMS expects plates to be scraped only after the whole table is done. In dining rooms, plates are bussed to a cart or bus tub and scraped in the dish room. The capture point is **the bus cart or the dish-return window, before scraping**. Scraping at the table would destroy the "after" image (practice inference, [U]).

## 2. The main plate

| Feature | Finding | Source |
|---|---|---|
| Size | **9 in (about 230 mm) round entrée plate** is the healthcare standard. Heated bases and domes are sized for it. Examples: Aladdin Temp-Rite 9" bases ("most 9" round entree plates"), Dinex wax base for 9" plates, Dinex Tropez 9.5" dome. Carlisle Durus 9" wide-rim melamine. Schönwald "Donna Senior" 9.5" porcelain. | [Aladdin base](https://www.hospitalitysuperstore.com.au/product/aladdin-temp-rite-9-230mm-heat-on-demand-ultra-bases), [Dinex/KaTom](https://www.katom.com/learning-center/healthcare-food-delivery-dinex.html), [Dinex dome](https://www.imperialdade.com/catalog/product-detail/dinex-tropez-plate-cover-9-50x2-25-in-plastic-dark-blue-12-case-cfs%20brands-DX9400B50?id=28320), [Carlisle](https://www.howdybrewer.com/products/carlisle-foodservice-products-plate-9-wr-sierra-sand-sand-43013908), [Webstaurant](https://argo.webstaurantstore.com/47105/healthcare-dishware.html) |
| Restaurant-style dining rooms | May use 10–11 in china (practice, [U]). | — |
| Color | Healthcare dishware is mostly **solid, unpatterned** (retailer note). White or cream china is the default (practice, [U]). **High-contrast colored plates** for dementia: Dunne 2004 (9 men, advanced AD) found red dishes raised food intake 25% and liquid intake 84%. A follow-up found high-contrast blue also worked and low-contrast colors did not. Small n, but widely adopted. | [Dunne 2004](https://pubmed.ncbi.nlm.nih.gov/15297089/), [Webstaurant](https://argo.webstaurantstore.com/47105/healthcare-dishware.html) |
| Divided or scoop plates | Adaptive plates (high-sided "Dignity" plates, scoop plates, divided portion plates) are used for individual residents per OT or care plan, and F810 requires them when ordered. No prevalence data found [U]. Expect a minority. | [CMS-20053 F810](https://qsep.cms.gov/data/168/CMS-20053Dining.pdf), vendor pages |
| Covers and bases | Room trays use a heated base (wax, pellet or induction), an underliner, the plate, and a dome. Bowls and mugs often have lids. The dome comes off before eating. "After" images need the lid off too. | Dinex, Aladdin above |
| Disposable vs china | CMS F550 checks for "nondisposable cutlery and dishware". Surveyors have cited disposable plates and trays. **China or melamine is the norm.** Disposables appear in isolation rooms or outbreaks (practice, [U]). | [CMS-20053](https://qsep.cms.gov/data/168/CMS-20053Dining.pdf), [NC 2567](https://info.ncdhhs.gov/DHSR/facilities/nh/2019/20190417-955030.pdf) |

What this means for the model:
- Train on a round plate of about 9 in (about 23 cm).
- Plate color: white or cream first, then add red, blue and melamine colors (augment or collect data).
- Use the plate's known diameter as a scale reference.
- Treat divided and high-sided plates as edge cases.

## 3. How staff record intake today

- **One number per meal, not per item.** A real facility policy, "Percentage of Foods Consumed" (Windsor House, OH, 2010):
  - "Nursing staff will record the percentage of meals consumed by each resident after each meal."
  - Scale: 0 / 25 ("approx. 25% of entrée or 50% of one item") / 50 ("ate 50% of the entrée or 25% of the vegetable and the soup is left") / 75 / 100.
  - "**Milk and juice will be included in the total meal intake.**"
  - "Supplements… are tracked separately."
  - [Policy PDF](https://g5-assets-cld-res.cloudinary.com/image/upload/v1709864149/g5/g5-c-5qfsxarys-windsor-house/g5-cl-1ltoutkunj-windsor-house-girard-oh/uploads/Percentage_of_Foods_Consumed_ra1fvc.pdf) (text read from the PDF).
  - **Takeaway:** the score is a gut-feel average over the whole tray, anchored on the entrée.
- PointClickCare POC: one % per meal in 25% steps (see market-research §1.7).
- **Per-item intake** is recorded only in an RD-ordered **calorie count**, usually 3 days, done by hand on a menu sheet (practice, [U]; no primary form found).
- **MDS 3.0 has no per-meal intake item.**
  - Section K tracks swallowing (K0100), height and weight (K0200), weight loss and gain (K0300/K0310), nutritional approaches (K0520) and tube share (K0710). See nursing-home-rules §2.
  - The "<75% of most meals" low-intake line is the old MDS 2.0 / OBRA trigger.
  - F692 surveyors review "meal monitors" as evidence, not as a required format.
- AFINI-T authors: a bulk %-per-plate "assumes an even distribution across the foods offered on the plate… if 50% … was consumed, there is no way to know if it was the protein or the vegetable". LTC needs "an intake breakdown for each item consumed (not averaged across a plate)" ([arXiv 2112.04608](https://arxiv.org/pdf/2112.04608)).

What this means for us:
- Per-item intake on the **main plate** already beats today's per-meal number.
- Report one meal % (weighted toward the entrée) so it fits the existing EHR field.
- Side items (soup, milk, dessert) feed into the official %. Missing them is a known gap: flag it, don't hide it.
- Protein mostly sits on the main plate (entrée). Milk is the main exception: about 8 g per cup per USDA (common knowledge, check before quoting).

## 4. Texture-modified diets on the plate

| Fact | Number | Source |
|---|---|---|
| Residents on puree, Florida LTC survey (97 facilities) | **About 14%** of residents on average (mean 17 per facility). Puree served in 99% of homes. Ground or minced texture served in 85%. | [Annals of LTC, FL survey](https://www.hmpgloballearningnetwork.com/site/altc/articles/survey-modified-texture-food-and-beverage-practices-long-term-care-facilities-florida) |
| Any modified texture, Canada M3 (32 homes, n = 639) | **About 47%** (pureed, minced & moist, soft & bite-sized) | [Vucea 2019 CJDPR](https://dcjournal.ca/doi/10.3148/cjdpr-2018-045) |
| Range across CA/US/AU studies | 26–67% | review cited in [Burger 2019](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6806511/) |
| How puree looks | Mostly **scoops**: round mounds from numbered dishers, or puree served in ramekins. Florida: only **14.6%** mold in-house and 3.1% buy pre-molded. Molded puree is shaped with silicone molds plus a gelling agent. | FL survey, [Shape It](https://shapeit.flavourcreations.com.au/resources/), [JHN pilot](https://www.citedrive.com/en/discovery/patient-nutritional-intake-and-experiences-with-two-models-of-texture-modified-food-preparation-in-hospital-a-pilot-study/) |
| AFINI-T dataset | Modified-texture foods were imaged as **a single item on a plate** (93 foods, 665 plates). Multi-item puree plates were left for future work. | [arXiv](https://arxiv.org/pdf/2112.04608) |

What this means for us:
- A puree plate is about 3 colored mounds on a 9 in plate, often from the same scoop sizes.
- Color separates the items. Depth gives the mound height.
- Keep puree in the v1 scope statement as "supported in data roadmap", not in the live demo, unless we stage one puree plate.

## 5. What existing intake cameras photograph

| System | Unit of capture | Source |
|---|---|---|
| **AFINI-T** (Waterloo, LTC) | **One plate**, top-down in an imaging cage. Regular texture: 3 foods per plate. Modified texture: 1 per plate. | [arXiv](https://arxiv.org/pdf/2112.04608) |
| **Meal Vision** (Compass AU, aged care) | **One personalised plate** with an RFID tag, scanned before and after | [Deloitte](https://www.deloitte.com/au/en/services/consulting/case-studies/ingenious-ai-combatting-malnutrition-optimising-nutrition-australia.html) |
| Pouyet 2015 (4 French NHs) | **Plate** images after the meal vs one reference plate | via [Billeret 2023](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9920108/) |
| Billeret 2023 SEFI-AP (FR NH) | Plate photos before and after | [Nutrients](https://www.mdpi.com/2072-6643/15/3/646) |
| foodintech (FR hospital/EHPAD) | Overhead, each dish, QR on tray. Weakest on bowls: yogurt and puree. | market-research §1.3 |
| **Nuvilab Nutri-Guard** (hospital) | **Whole returned tray**: "Capture the returned tray" | [Nuvilab](https://www.nuvilab.com/nutri-guard) |
| Simmons & Reuben 2000 (US NH) | Before/after meal photos, scored as **total %** per meal by a nutritionist. Unit (tray or plate) not confirmed [U]. | [AAFP summary](https://www.aafp.org/afp/2000/0801/p637a) |

Pattern:
- LTC-specific systems are **plate-first**.
- The hospital system (Nuvilab) is **tray-first**, because US and Asian hospitals still run tray lines.

## 6. Recommendation

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Single main plate | Matches dining-room service, AFINI-T and Meal Vision. Carries the entrée and protein signal. Simple scale reference (9 in plate). Doable live demo. | Misses soup, milk and dessert, which do count in the facility %. | **v1 model + demo** |
| Whole tray | Matches room trays and hospitals (Nuvilab). | CMS discourages trays in dining rooms. More classes, occlusion from lids, cups and cartons. Slower to label. Riskier demo. | Not v1 |
| Main plate + side bowls | Closest to the official % | Needs container detection plus per-bowl depth. Bowls are the known failure (foodintech, Fukui). | **v2. Rig ready for it now.** |

Concrete build choices:
- Overhead camera at the bus cart or dish-return window. FOV about 50 × 40 cm (a full tray) [U, tray size is practice]. One plate placed in a marked zone, with the QR ticket beside it.
- Classes for v1: plate (container) + food items (protein / starch / vegetable or specific menu items). Optional "side vessel present" flag so the system can say "sides not measured".
- Output: per-item % on the plate, plus a meal % with the entrée weighted most, mapped to the 0/25/50/75/100 bucket.

### Slide text (scope)

> **Scope (v1): the main plate.**
> Top-down camera at dish return. One 9-inch plate per scan, before and after.
> Per-item % eaten for entrée, starch and vegetable, which carry most of the protein.
> Why the plate: most senior dining is now plated, and CMS treats trays in the dining room as institutional. Today's charting is one gut-feel number per meal, anchored on the entrée.
> **Next (v2):** side bowls, cups and milk in the same camera view (the rig already frames a full tray), plus puree mounds (14–47% of residents are on modified textures).

## Open / unverified
- Share of meals eaten in rooms vs the dining room in US SNF and AL: no data found.
- Whether CMS-20053 still names trays as a problem in a newer revision: confirmed in the 10/2022 form only.
- Prevalence of colored or adaptive plates in US LTC: no data.
- Standard per-item calorie-count form: no primary source found.
- Tray dimensions (assumed about 14×18 to 15×20 in): not confirmed.
