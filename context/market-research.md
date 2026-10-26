# Intake.ai: market and competitive research

Researched 2026-10-25 for the Roboflow FE live demo (Wed 2026-10-28).
Rule used here: every fact has a link. "(vendor claim)" means the company said it and nobody checked it. "(unverified)" means one weak source or none.

## TL;DR

1. **The idea is not new. It is proven in research and still early in products.** Before/after tray imaging for intake has been studied since the 2000s in Japan ([Kochi Tech JST report](https://www.jst.go.jp/innovate/innovative/pdf/61179.pdf)) and in 2019-2022 at Bern ([Lu et al.](https://arxiv.org/abs/2003.08273)) and Waterloo, where AFINI-T reported a mean intake error of -0.4 mL ± 36.7 mL ([Pfisterer 2022](https://aging.jmir.org/2022/4/e37590/)).
2. **Closest product, LTC: Meal Vision** (Compass Group Australia + Deloitte + AerVision). It uses a camera, LiDAR and RFID-tagged plates, scans before and after, runs on AWS, and sends alerts. It is in "more than a dozen" aged care dining rooms ([Consultancy.com.au](https://www.consultancy.com.au/news/7315/compass-partners-with-deloitte-on-ai-tool-for-aged-care-nutrition)). It has published no accuracy numbers.
3. **Closest product, hospitals: Nuvilab** (Korea). It has a 2D+depth scanner, a Singapore pilot that claimed 95% accuracy ([iTnews Asia](https://www.itnews.asia/news/alexandra-hospital-uses-ai-to-track-patient-nutrition-intake-603809)), a US tray-check product with Morrison Healthcare, and a new intake product, Nutri-Guard. Its own hospital validation is "in progress" ([Nuvilab](https://www.nuvilab.com/nutri-guard)). Nuvilab says LTC comes next ([Unicorn Factory](https://www.unicornfactory.co.kr/article/2025122313282994632)).
4. **Other live players:** foodintech/Trayvisor (France: hospitals and EHPAD nursing homes), ALPINA+SANA (Switzerland: 3D camera in hospitals), Doliggy "Meshipasha" (Japan: 5-resident pilot in 2026), Skeal and LogMeal (tablet apps). Waste-vision companies (Winnow, Leanpath, Orbisk, Kitro, Raccoon Eyes) measure the bin, not the person.
5. **In the US LTC market, no shipping camera intake product was found.** Staff still eyeball each plate in 25% steps and type it into the EHR ([PCC CNA guide](https://practicetestgeeks.com/cna/pointcare-click-cna)). Those staff estimates run about 20 points too high ([Pokrywka 1997 via AAFP](https://www.aafp.org/afp/2000/0801/p637a)).
6. **Market:** 14,742 CMS-certified nursing facilities with about 1.24M residents ([KFF 2025](https://www.kff.org/medicaid/a-look-at-nursing-facility-characteristics/)). The workforce is still below its pre-pandemic level and 90% of facilities report hiring trouble ([AHCA via SNN](https://skillednursingnews.com/2026/01/ahca-nursing-homes-added-40700-jobs-in-2025-as-turnover-agency-use-declined/)). A capable edge box costs $249 ([Tom's HW](https://tomshardware.com/tech-industry/artificial-intelligence/nvidia-launches-new-usd249-ai-development-board-that-does-67-tops)).
7. **Honest wedge:** per-item intake joined to a US tray ticket, protein-first alerts on streaks, on-site edge processing (no images leave the building), and a published accuracy method checked against a 1 g scale. Do not claim "first".

---

## 1. Healthcare intake tracking (closest bucket)

### 1.1 Meal Vision: Compass Group Australia + Deloitte + AerVision
- **Status:** product, early rollout. **Country:** Australia. **Setting:** residential aged care serveries.
- **How it works:**
  - The scanning unit has a high-res camera, an RFID reader and LiDAR.
  - Each resident's plate carries an RFID tag. The plate is scanned before and after the meal.
  - Food is identified and its volume measured.
  - Data goes to an AI platform on AWS.
  - Alerts reach carers, caterers and medical teams. Families can see the data.
  - Source: [Deloitte case study](https://www.deloitte.com/au/en/services/consulting/case-studies/ingenious-ai-combatting-malnutrition-optimising-nutrition-australia.html).
- **Scale:**
  - "More than a dozen" aged care dining operations and "hundreds" of residents as of May 2023 ([Consultancy.com.au](https://www.consultancy.com.au/news/7315/compass-partners-with-deloitte-on-ai-tool-for-aged-care-nutrition)).
  - Award entries say about 50 units were built (vendor claim, [Cannes Lions entry](https://lovethework.com/work-awards/entries/meal-vision-682553); figure seen only in a search snippet, so unverified).
- **Accuracy:** none published. The only claim is "more accurate than possible by a human" (vendor claim, Deloitte).
- **Business model:** used inside Compass's own catering contracts. No public price.
- **Pitch context:**
  - Australia's Royal Commission found 68% of residents malnourished or at risk ([Compass](https://compass-group.com.au/meal-vision/)).
  - Australia's strengthened Quality Standards, in force from 1 Nov 2025, include **Standard 6: Food and nutrition** ([health.gov.au](https://www.health.gov.au/node/49147)).
- **Status after 2024:** no news found (unverified whether it is still expanding).

### 1.2 Nuvilab: AI Food Scanner, Nutrition AI, Nutri-Guard AI
- **Status:** product. **Country:** South Korea, expanding to the US and Singapore. **Settings:** schools, daycare centers, hospitals, corporate cafeterias.
- **How it works:**
  - Uses 2D cameras, 3D depth sensors and multimodal AI.
  - Scans the tray before and after the meal. No scale needed.
  - Scan time is about 1 s ([NutritionInsight](https://www.nutritioninsight.com/news/innovative-food-tech-nuvilabs-ai-meal-scanners-boost-healthy-nutrition.html); [Hankyung CES 2023](https://www.hankyung.com/amp/202301066919i)).
- **Hospital track:**
  - **Alexandra Hospital, Singapore:** 7-week pilot. 95% average accuracy against weighed food and nurse charting. The hospital plans scanners across its 1,400-bed build-out by 2028 ([iTnews Asia, Jan 2024](https://www.itnews.asia/news/alexandra-hospital-uses-ai-to-track-patient-nutrition-intake-603809)).
  - **US, with Morrison Healthcare (Compass Group USA):** "Nutrition AI" checks the tray *before* it goes out (right diet, allergens). It does not measure what was eaten ([galvnews / BusinessWire, Mar 2026](https://www.galvnews.com/healthcare-digital-wins-2026-artificial-intelligence-excellence-award-for-nutrition-ai-developed-in-collaboration-with/article_916c8e7b-e225-5c68-bf5c-e588750d8a82.html)).
  - A "26 US hospitals, 20k meals/day" figure appeared only in a search summary (unverified).
  - **Nutri-Guard AI:** staff photograph the returned tray. Outputs are per-item intake, energy, protein, and flags for "sustained intake gaps". Validation is "in progress". It has a Canadian hospital partner and an "elder care longitudinal research" reference ([nuvilab.com/nutri-guard](https://www.nuvilab.com/nutri-guard)).
  - At HIMSS 2026, Nuvilab pitched intake data for **malnutrition coding and reimbursement** ([HIMSS exhibitor page](https://app.himssconference.com/event/himss-2026/exhibitor/RXhoaWJpdG9yXzIzOTAxNDM=)).
- **Scale:**
  - About 1,100 institutions in Korea ([Unicorn Factory, Dec 2025](https://www.unicornfactory.co.kr/article/2025122313282994632)).
  - "1,000+ global clients, 100k users" and "98% accuracy in 0.3 s" (vendor claim, [PR Mar 2026](https://www.placera.se/pressmeddelanden/naver-d2sf-makes-follow-on-investment-in-nuvilab-ai-nutrition-analytics-startup-20260331)).
- **Funding:**
  - KRW 10B Series A in 2022 ([MT](https://www.mt.co.kr/future/2022/10/08/2022100716013995843)).
  - NAVER D2SF bridge round in 2026 ([PR](https://www.placera.se/pressmeddelanden/naver-d2sf-makes-follow-on-investment-in-nuvilab-ai-nutrition-analytics-startup-20260331)).
  - CB Insights lists $8.3M total ([CB Insights](https://www.cbinsights.com/company/nuvi-lab)).
- **LTC plans:** the CEO plans to expand to nursing facilities next ([Unicorn Factory](https://www.unicornfactory.co.kr/article/2025122313282994632)).
- **Cloud vs edge:** not stated. The platform is cloud analytics (unverified).

### 1.3 foodintech (Atol CD + Nutrisens + Trayvisor), France
- **Status:** product, national rollout announced in 2023. **Origin:** CHU Dijon, 2016. **Settings:** hospitals and EHPAD (French nursing homes).
- **How it works:**
  - A camera mounted overhead photographs each dish before and after the meal.
  - A QR code on the tray links the two photos.
  - In EHPADs, a tablet on the meal cart selects the resident.
  - Source: [Restauration Collective 2023](https://www.nutrisens.com/wp-content/uploads/2023/05/Restauration_Collective_20230331100000.pdf).
- **Accuracy:**
  - Tested on 22,544 situations covering 149 dishes.
  - Reliability (ICC) was excellent for 39% of dishes and good for 19%.
  - Yogurts and purées were the weakest, because a single overhead view cannot see height.
  - Source: [Van Wymelbeke-Delannoy, Nutrients 2022](https://www.mdpi.com/2072-6643/14/1/221).
- **Note for us:** this is RGB-only, and depth is exactly where it failed. That supports our depth choice.

### 1.4 ALPINA+SANA (Alpinasana AG), Switzerland
- **Status:** pilot or early product. **Founders:** from ETH Zurich and HSG. **Settings:** hospitals and nursing homes.
- **How it works:**
  - A 3D camera with laser volume measurement scans the meal at kitchen dispatch.
  - An identical camera scans it at tray return. The volume difference is the intake.
  - About 30k reference images.
  - Sources: [CITI I/O 2025](https://news.citi.io/2025/03/16/reducing-malnutrition-in-hospitals-with-ai-cameras/), [Blick 2024](https://www.blick.ch/wirtschaft/neues-tool-der-eth-ki-erkennt-jetzt-auch-mangelernaehrung-id19687660.html).
- **Pilots:**
  - Waidspital Zürich in 2024. Frauenfeld, Emmental and St. Gallen planned for 2025.
  - "About 70 hospitals in talks" (vendor claim, Blick).
  - An Innosuisse project on care facilities won the HSG Impact Award 2026 ([HSG](https://www.unisg.ch/de/videodetail/news/hsg-impact-award-2026-ki-basierte-erfassung-von-mangelernaehrung/)).
- **Business model:** the tracker plus medical-nutrition foods (protein ice cream in 20+ hospitals). The data feeds the supplement sale.
- **Accuracy:** not published.

### 1.5 Japan
- **Doliggy "Meshipasha" (めしパシャ)**, a Ritsumeikan University spin-off. Staff photograph the tray before and after the meal, and AI estimates the amount eaten, nutrients and kcal. The pilot covers about 5 residents in serviced senior housing in Osaka, from 28 Jan 2026 for 5 weeks. No accuracy published ([Osaka City](https://www.city.osaka.lg.jp/hodoshiryo/keizaisenryaku/0000670658.html)).
- **SOMPO Care + NEC (2020, stalled):**
  - Before/after photos and AI intake for 21 nursing home residents over 5G.
  - Puréed food was hard to recognize.
  - It needed a camera plus an on-site server costing "several million yen".
  - SOMPO estimated ¥120M in savings across 150 facilities.
  - "Several more trials needed" ([Newswitch](https://newswitch.jp/p/21341)). No later news found.
- **Tokushima University Hospital:**
  - An AI model for leftover liquid food scores 0-100% in 10% steps.
  - AI error 0.85 vs 1.03 for dietitians' visual estimates, P=.009 ([JMIR Form Res 2024](https://formative.jmir.org/2024/1/e55218/)).
  - The team is building an automatic tray-photo device ([project PDF](https://www.tokushima-hosp.jp/system/data/ftp/ftp/20230828085632_1403_5.pdf)).
- **Fukui University:** a pre/post image pair system for inpatients. Depth inside bowls caused large errors ([PDF](https://lifeseimei.med.u-fukui.ac.jp/wp/wp-content/uploads/2023/09/b9bcd1cbb1084dc696288df5585bb75f.pdf)).
- **Canon patent US11763437:** see section 6.

### 1.6 Other hospital and LTC efforts
| Name | Org / country | Status | How | Evidence |
|---|---|---|---|---|
| Bern RGB-D system | ARTORG, Univ. Bern + Inselspital, CH | research | Intel RealSense RGB-D before/after; segmentation, few-shot classifier, 3D surface | 322 meals; correlation >0.91; mean relative error <20% ([Lu et al. 2020](https://arxiv.org/abs/2003.08273)); in geriatric acute care it agreed better with experts than the ward's standard method ([Papathanail, Nutrients 2021](https://europepmc.org/articles/PMC8706142)) |
| AFINI-T | U. Waterloo, Schlegel-UW RIA, UHN, Canada | research, no spin-out found | RGB-D after-meal image vs reference portion; per-item; regular and texture-modified food | 88.9% top-1; -0.4 mL ± 36.7 mL; nutrients r² 0.92-0.99 vs mass; simulated LTC plates ([JMIR Aging 2022](https://aging.jmir.org/2022/4/e37590/)); "within 5%" vs staff "≥50% error" ([UWaterloo](https://uwaterloo.ca/artificial-intelligence-institute/news/food-tracking-ai-system-developed-reduce-malnutrition-ltc)) |
| FlavoriaFlex | Univ. Turku, Finland | research | Camera kiosk, before/leftover images, item-level kcal and macros | 6-day ward deployment; 94% recognition (F1 0.76); 31 of 133 trays never came back ([AHFE 2026](https://openaccess.cms-conferences.org/publications/book/978-1-964867-87-8/article/978-1-964867-87-8_2)) |
| Grenoble prototype | CHU Grenoble Alpes, France | research | AI image device on hospital trays | CCC 0.957 starches, 0.845 meat, 0.767 veg; bias -12 g / +1 g / -15 g vs weighing ([Albaladejo, Clin Nutr ESPEN 2025](https://hal.univ-grenoble-alpes.fr/hal-04749965v1)) |
| Padua pilot | Univ. Padua, Italy | research | AI before/after tray images vs weighing vs nurse diaries; vendor not named | 362 meals, 67 patients; AI MAE ≈40 g (≈10% of tray), underestimates; nurse diaries matched only 60.8% ([Favaretto, Nutrients 2026](https://research.unipd.it/handle/11577/3603762)) |
| Southampton plate imager | Univ. Southampton, NIHR BRC, Serco, UK | research | Camera, screen, tray holder with weight sensor and QR, before/after | no metrics yet ([NIHR BRC 2025](https://www.southamptonbrc.nihr.ac.uk/post/ai-being-used-to-prevent-malnutrition-in-hospital)) |
| DIMS | Aalborg Univ., Denmark | research (2014) | Camera, scale and IR thermometer before/after on ward | pilot on a GI ward ([AAU](https://capfoods.aau.dk/technical/FoodScapeLab/DIMS)) |
| Skeal | (country unverified) | product | Tablet/phone photo; served vs eaten; waste | 4 pilots claimed (vendor claim) ([skeal.co](https://www.skeal.co/)) |
| LogMeal | Spain (unverified) | API product | Photo food recognition; markets intake tracking for care homes | no LTC deployment found ([logmeal.com](https://logmeal.com/)) |
| TrayVerify | Baltimore, US | startup | Camera checks the tray *before* delivery against the diet order; no intake | ([TinyTech Fund](https://www.tinytechfund.com/company/trayverify-ai-inc)) |

### 1.7 EHR and dietary software in US LTC: where intake lives today
- **PointClickCare:** the dominant LTC EHR.
  - "~75% of providers, ~17,000 facilities" (undated, unverified; [IntuitionLabs](https://intuitionlabs.ai/articles/pointclickcare-ehr-long-term-care)).
  - CNAs chart percent of meal eaten for breakfast, lunch and dinner in POC, usually in 25% steps ([guide](https://practicetestgeeks.com/cna/pointcare-click-cna); [template](https://www.mangoapps.com/templates/tasks/resident-meal-intake-percentage-log)).
  - It records **one number per meal, not per item, and no protein**.
- **MatrixCare MealTracker:** menus, tray tickets, calorie counts, nutrient analysis and malnutrition alerts ([MatrixCare brochure 2026](https://www.matrixcare.com/wp-content/uploads/2026/06/SLTC-BRO-MealTracker-Online-Ordering-May-2026-11x8.5-FNL-digital.pdf)). Intake still comes from manual entry (unverified).
- **MealSuite:** ordering, tray tickets, resident diet profiles, weight graphs. No camera intake found ([IntuitionLabs](https://intuitionlabs.ai/software/assisted-living-senior-living/dietary-and-nutrition-management/mealsuite)).
- **CBORD / Computrition:** hospital-centric. CBORD has drifted away from LTC (competitor's 10-K view, 2013, [SEC](https://www.sec.gov/Archives/edgar/data/0001517391/000114420413022099/v341203_10-k.htm)).
- **Takeaway:** these vendors **produce the tray ticket** that Intake.ai reads, and **receive the intake data** Intake.ai would produce. They are partners or acquirers before they are competitors.

---

## 2. Food-waste vision (measures waste in the bin, not intake per person)

| Name | Country | Sensors / location | Scale, evidence | Funding |
|---|---|---|---|---|
| Winnow (Vision, "Throw & Go") | UK | Camera over kitchen bin + scale | IKEA, Hilton, Accor; claims 40-70% waste cut (vendor claim) ([EU-Startups](https://www.eu-startups.com/?p=87003)); bought Lumitics Jul 2026 ([startupresearcher](https://www.startupresearcher.com/news/winnow-acquires-singapore-based-lumitics-in-food-waste-tech-deal)) | $12M Series B + $8M EIB ([The Spoon](https://thespoon.tech/winnow-raises-12m-series-b-round-to-fight-food-waste-in-commercial-kitchens/)) |
| Lumitics (Insight) | Singapore | Bin sensor + image recognition; Etihad trial on returned airline meals ([FTE](https://www.futuretravelexperience.com/2020/09/etihad-trials-computer-vision-and-machine-learning-to-reduce-food-waste/)) | Hyatt, Four Seasons, 20+ countries | acquired by Winnow |
| Leanpath (360 AI) | US | Staff put waste on a scale under a camera | 4,500 kitchens, 45 countries (vendor claim); hospitals incl. KU Med ([Leanpath blog](https://blog.leanpath.com/leanpath-ai-enabled-food-waste-tracking)); Forefront senior living/healthcare sites ([Waste360](https://www.waste360.com/food-waste/forefront-leanpath-partner-on-ai-enabled-food-waste-management)); ~$1,200/mo ([FAO](https://agritechobservatory.review.fao.org/ar/leanpath), unverified) | ~$8M ([CB Insights](https://www.cbinsights.com/company/leanpath)) |
| Orbisk | Netherlands | Camera + scale on bin | ~500 sites; Accor, Hyatt, Carnival (vendor claim) | ~$8-9M Series A Dec 2024 ([CB Insights](https://www.cbinsights.com/compare/kitro-vs-orbisk)) |
| Kitro | Switzerland | Camera over bin + weight | 100+ devices, 40 sites; EPFL 30 devices ([CB Insights](https://www.cbinsights.com/compare/kitro-vs-orbisk)) | $3.6M-$12M (conflicting) |
| Raccoon Eyes AI | US (Georgia Tech spin-out) | **Camera at dish return** photographs every plate; type + weight of leftovers | UGA dining: -21% waste ([Grady](https://gradynewsource.uga.edu/uga-addresses-on-campus-food-waste-with-new-sustainability-initiatives/)); 90% accuracy (vendor claim, [Hypepotamus](https://hypepotamus.com/startup-news/raccoon-eyes-tackles-food-waste/)); annual B2B license ([Causeartist](https://www.causeartist.com/raccoon-eyes-ai/)) | bootstrapped + Village Capital |
| Foodfx (ex-Skoopin) | US | Mobile tracker: load cells + RGB + depth; before/after service in cafeterias | patent US12688719 ([Google Patents](https://patents.google.com/patent/US12688719B1/en)) | (unverified) |
| Nuvilab (school mode) | Korea | Before/after tray scan at school lunch | one high school cut waste 55.7% in 2 years (vendor claim, [Future Chosun](https://futurechosun.com/archives/77216)); Ourhome catering MOU Jan 2026 ([eToday](https://www.etoday.co.kr/news/view/2546273)) | see 1.2 |
| China canteens | China | Smart canteens: AI dish recognition at checkout, nutrition shown on screen | Capital Normal Univ. study: plate camera at return, -13% waste (unverified, from search snippet); CAU -48.5% waste ([champions123](https://champions123.org/case-study-china-agricultural-university-cuts-food-waste-nearly-50)) | n/a |

- **Not vision:** Too Good To Go (surplus marketplace) and Wasteless (dynamic pricing). Both are out of scope.
- **Pattern:** these products only need **kg per food category per site**. Intake.ai needs **grams per item per resident per meal**, linked to identity and care plan. That is a harder problem with a different buyer: the DON (Director of Nursing) and the RD (registered dietitian), not the chef.

## 3. Cafeteria checkout vision (could pivot to intake)
- **Mashgin** (US): camera kiosk that recognizes items, including plated food.
  - $62.5M Series B, $1.5B valuation (2022).
  - Customers include Aramark, NFL and MLB venues ([VCJ](https://www.venturecapitaljournal.com/mashgin-inks-62-5m-series-b/)).
  - It does item recognition only. No volume, no after-scan.
- **auvisus** (Germany, KIT spin-off): tray-under-camera checkout in canteens ([KIT](https://www.ksop.kit.edu/auvisus.php)).
- **Trayvisor** (France): canteen checkout vision, and also the foodintech hospital partner ([Motherbase](https://demo.motherbase.ai/startup/195791-trayvisor)). **It has already pivoted from checkout to intake.**
- **Proppos FastPay** (Spain, edge AI) and **MCR AI Self-Scan** (UK) ([MCR](https://www.mcr-systems.co.uk/symphony-solutions/innovation/self-service-tray-scanning/)).
- **BakeryScan** (Brain Co., Japan): over 400 bakeries, about $20k per unit ([Business Reporter](https://www.business-reporter.co.uk/management/the-cash-register-that-can-tell-a-croissant-from-a-donut-by-sight)).
- **China:** smart-canteen vendors such as 乐牛 show protein and kcal at checkout ([CSDN](https://gitcode.csdn.net/6a2fc10f662f9a54cb7f6dfa.html)). Hangzhou elderly canteens use AI dish recognition ([Hangzhou news](https://hznews.hangzhou.com.cn/xinzheng/quxian/content/2020-11/18/content_7855717.htm)). That is nutrition *served*, not *eaten*.
- **Hitachi / Fujitsu:** no cafeteria tray-recognition product found (unverified).
- **Takeaway:** checkout players already own camera hardware above trays. Adding an after-scan is a short step, as Trayvisor shows. They lack identity, care plans and clinical alerts.

## 4. Consumer and clinical photo apps (context only)
- **Nutrition5k (Google, CVPR 2021):** 5k dishes with depth.
  - Depth-volume input cut mass error from 18.7% to 13.7%.
  - End-to-end kcal MAE was 16.5% ([Thames et al.](https://arxiv.org/abs/2103.03375)).
- **SnapCalorie:** founded by a Google Lens co-founder. Uses iPhone LiDAR. Claims ±80 kcal on a 500 kcal dish (vendor claim). Raised $2M ([TechCrunch](https://techcrunch.com/?p=2561037)).
- **App accuracy is poor:**
  - MyFitnessPal and Fastic were the best of 7 AI apps, but energy estimates were still "inaccurate" ([Li et al., Nutrients 2024](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11314244/)).
  - An NIH abstract found 4 apps underestimated meals by 250-345 kcal ([Epocrates](https://www.epocrates.com/online/article/ai-calorie-counting-apps-miss-a-third-of-meal-calories)).
- **Remote Food Photography Method (Pennington):** underestimated energy intake by less than 6-7% vs weighed food ([PMC](https://pmc.ncbi.nlm.nih.gov/articles/PMC3975169)).
- **Not researched further:** Foodvisor, Calorie Mama, Passio, Bitesnap and Keenoa are consumer or dietitian tools that need the person to hold a phone. **That is a non-starter in LTC.**

## 5. Academic research: key papers and datasets
| Work | Setting | Sensor | Key number |
|---|---|---|---|
| Pfisterer, *Sci Rep* 2022 (EDFN-D) | LTC (simulated) | RGB-D | IoU 0.879; shows area ≠ volume ("visual-volume discordance") ([Nature](https://www.nature.com/articles/s41598-021-03972-8)); -4.2% mean intake error per secondary summary (unverified) |
| AFINI-T, *JMIR Aging* 2022 | LTC (simulated, 1,039 plates) | RGB-D | -0.4 ± 36.7 mL; 88.9% top-1 ([link](https://aging.jmir.org/2022/4/e37590/)) |
| Lu et al., IEEE TMM 2020 | Hospital, 322 meals | RGB-D | r > 0.91, MRE < 20% ([arXiv](https://arxiv.org/abs/2003.08273)) |
| Papathanail, *Nutrients* 2021 | Geriatric acute care | RGB-D | beat the standard ward method vs experts ([EPMC](https://europepmc.org/articles/PMC8706142)) |
| FoodIntech, *Nutrients* 2022 | Hospital | RGB overhead + QR | excellent ICC for only 39% of dishes ([MDPI](https://www.mdpi.com/2072-6643/14/1/221)) |
| Albaladejo 2025 / Favaretto 2026 | Hospital wards | RGB | 1-15 g bias; ≈10% MAE (see 1.6) |
| Tokushima, JMIR 2024 | Hospital liquids | RGB | AI beat dietitians (0.85 vs 1.03) |
| Nutrition5k 2021 | Cafeteria | RGB-D overhead | kcal MAE 16.5% |
| **Datasets:** UNIMIB2016 (trays, before/after) ([V7](https://www.v7labs.com/open-datasets/unimib-food-database)); FLIC 2026 (401 full/leftover tray pairs with mass, Italian canteen) ([Piccoli, Appl Sci 2026](https://boa.unimib.it/handle/10281/624021)); EcoPlate (313 Indian mess before/after pairs, waste % per item) ([IEEE DataPort](https://ieee-dataport.org/documents/ecoplate-paired-multimodal-dataset-indian-cafeteria-food-instance-segmentation)) | | | |

- **Staff baseline, the number to beat:**
  - US nursing homes: staff recorded about 79% intake vs 59% by trained observers ([AAFP summary of Pokrywka 1997](https://www.aafp.org/afp/2000/0801/p637a)).
  - Hospitals: 44% of meals charted wrong (Palmer 2015, cited in [JMIR 2024](https://formative.jmir.org/2024/1/e55218/)).
  - Padua: nurse diaries matched only 60.8% ([link](https://research.unipd.it/handle/11577/3603762)).

## 6. Patents (quick scan, not legal advice)
- **US11763437 B2, Canon Inc.:**
  - Priority 2019, granted Sep 2023, expires about 2041.
  - Handheld 2D camera, before/after tray images, meal-tag barcode.
  - Semantic segmentation, dish-size scale matching, then an area-ratio to volume-ratio table per food and serving state.
  - Depth (ToF) is optional.
  - Explicitly about care facilities ([Google Patents](https://patents.google.com/patent/US11763437)).
- **Prior art it cites:** JP2008-204105 (automatic intake from before/after tray images) and JP2005-250885 (pattern projection 3D). **Before/after intake imaging itself is old prior art.**
- **US12688719 B1, Foodfx (ex-Skoopin):** filed 2024, granted Jul 2026. Scale + RGB + depth, container ID from the depth rim, before/after service. Cafeteria setting ([Google Patents](https://patents.google.com/patent/US12688719B1/en)).
- No Compass, AerVision or Nuvilab patent found (unverified; not searched in KIPO or IP Australia).
- **FTO note:** an RGB-D before/after volume difference plus a ticket join looks crowded but generic. Avoid copying Canon's specific area-to-volume conversion tables. Get real counsel before any commercial step.

## 7. Market context and why now
- **Size (US):**
  - 14,742 CMS-certified nursing facilities with about 1.24M residents; facility count down 6% over 10 years ([KFF 2025](https://www.kff.org/medicaid/a-look-at-nursing-facility-characteristics/)).
  - At 3 meals a day, that is about 1.36 billion resident-meals per year (our arithmetic).
- **Malnutrition prevalence (old, wide estimates):**
  - 35-85% of US residents in different studies ([APHA 2003](https://apha.confex.com/apha/131am/techprogram/paper_67442.htm); [Commonwealth Fund 2000](https://www.commonwealthfund.org/publications/fund-reports/2000/jul/malnutrition-and-dehydration-nursing-homes-key-issues-prevention)).
  - Chronic undernutrition in more than 12% of an MDS sample ([PubMed](https://www.ncbi.nlm.nih.gov/pubmed/17435960)).
  - About 54% in Canadian LTC ([Pfisterer 2022](https://www.nature.com/articles/s41598-021-03972-8)).
  - US data is sparse ([nutritionDay protocol](https://www.nutritionday.org/wp-content/uploads/2024_NH_Study_Protocol_V1_EN.pdf)). Quote ranges, not one number.
- **Cost:**
  - Disease-associated malnutrition costs $15.5B a year in direct US medical costs, $4.3B of it in the elderly ([Abbott-funded study via Abbott PR](https://abbott.mediaroom.com/2016-09-21-Malnutrition-Adds-15-5-Billion-Annually-to-Direct-U-S-Medical-Costs?asPDF=1); funder bias).
  - A Senate resolution cites $51.3B for older adults ([Murphy resolution](https://www.murphy.senate.gov/imo/media/doc/malnutrition_awareness_week_resolution.pdf), source not given).
- **Regulatory pull:**
  - **F692 (nutrition/hydration) deficiencies** keep citing missed weight loss and late RD follow-up ([example 2567](https://www.in.gov/health/reports/QAMIS/ltccr/e2sh11_2567.pdf)).
  - Missing meal-percent charting gets cited too ([Indiana F842](https://www.in.gov/health/reports/QAMIS/ltccr/k02811_2567.pdf)).
  - The long-stay "lose too much weight" quality measure is public ([NQF](https://www.qualityforum.org/Projects/n-r/Nursing_Homes/NH-024-10.aspx)). California tied it to payment in 2024 ([DHCS](https://www.dhcs.ca.gov/services/Documents/PL-24-006-SNF-WQIP-Weight-Loss-Measure-for-PY2-2024.pdf)).
  - Hospitals: the CMS Global Malnutrition Composite Score eCQM is in the IQR program since 2024 ([CDR](https://cdrnet.org/GMCS)).
- **Labor:**
  - The workforce is still 1.7% below pre-pandemic levels and 90% of operators struggle to recruit ([SNN Jan 2026](https://skillednursingnews.com/2026/01/ahca-nursing-homes-added-40700-jobs-in-2025-as-turnover-agency-use-declined/)).
  - The federal staffing minimum was repealed in Dec 2025 ([LeadingAge](https://leadingage.org/cms-repeals-nursing-home-minimum-staffing-standards/)), so there is no new mandated headcount. **Tools that save CNA minutes are the lever.**
- **Edge cost:**
  - Jetson Orin Nano Super costs $249 for 67 sparse / 33 dense INT8 TOPS ([Tom's HW](https://tomshardware.com/tech-industry/artificial-intelligence/nvidia-launches-new-usd249-ai-development-board-that-does-67-tops)).
  - Depth cameras are cheap too: our PoC uses an Orbbec DaBai DCW; for scale, a RealSense D435i costs about $320 (approximate, [CNX](https://www.cnx-software.com/news/realsense/?amp=1)). RealSense spun out of Intel in Jul 2025 ([Robot Report](https://www.therobotreport.com/intel-spins-out-realsense-as-standalone-company/)), a supply risk to watch.
  - Compare: SOMPO/NEC in 2020 needed a server costing "several million yen" ([Newswitch](https://newswitch.jp/p/21341)). Hardware cost is no longer the blocker.
- **Software market:** no credible LTC-dietary-software market size was found. Hospital nutrition software is about $1B by 2032 (analyst estimate, [QY via foriio](https://foriio.com/works/2248553)). Do not put a TAM number on the slide. Use facilities × meals.

---

## 8. Synthesis

### (a) Closest competitors vs Intake.ai
| | Setting | Sensors | Per-item? | Before/after | Nutrients | Alerts | Edge/cloud | Published accuracy | Price |
|---|---|---|---|---|---|---|---|---|---|
| **Intake.ai (PoC)** | US LTC, tray line | Overhead RGB + depth, QR ticket | yes | yes | protein + kcal | low-intake streaks | **edge (Jetson + Roboflow Inference)** | to be measured vs 1 g scale | n/a |
| Meal Vision | AU aged care | Camera + LiDAR + RFID plate | yes | yes | yes | yes | cloud (AWS) | none | in-contract |
| Nuvilab Scanner / Nutri-Guard | KR/SG/US hospitals, schools | 2D + depth (scanner); photo (Nutri-Guard) | yes | yes / after-only | kcal, protein | intake gaps | cloud (unverified) | 95% (SG, hospital-reported); validation pending | n/a |
| foodintech / Trayvisor | FR hospitals, EHPAD | Overhead RGB + QR | yes | yes | yes | dénutrition screening | (unverified) | ICC excellent for 39% of dishes | n/a |
| ALPINA+SANA | CH hospitals, care homes | 3D camera ×2 | yes | yes | yes | (unverified) | (unverified) | none | bundled with FSMP |
| Doliggy Meshipasha | JP senior housing | Phone photo | (unverified) | yes | yes | no | cloud app | none | pilot |
| Skeal / LogMeal | EU care, hospital, school | Tablet photo | yes | partly | yes | Skeal: yes | cloud | none | quote |
| Raccoon Eyes | US university dish return | Camera at conveyor | food type | after-only | no | no | (unverified) | 90% (vendor claim) | annual license |
| Winnow / Leanpath / Orbisk | Kitchens | Camera + scale on bin | category | after-only | no | no | cloud | waste-reduction claims | ~$1.2k/mo (Leanpath, unverified) |
| Mashgin / auvisus | Cafeterias | Camera(s) at checkout | yes | before-only | some | no | edge + cloud | none public | hardware + SaaS |
| AFINI-T / Bern (research) | LTC / hospital | RGB-D | yes | yes / after+ref | yes | no | lab | best published numbers | n/a |
| PCC / MatrixCare / MealSuite | US LTC | none (manual 25% steps) | no | no | some | weight-loss alerts | cloud | staff overestimate ~20 pts | incumbent SaaS |

### (b) What failed or stalled, and why
- **SOMPO + NEC (Japan, 2020):**
  - Puréed food broke recognition.
  - On-site servers costing several million yen.
  - Wi-Fi was hard to run in facilities.
  - It has been silent since ([Newswitch](https://newswitch.jp/p/21341)).
  - **Lesson:** handle texture-modified diets, and keep hardware cheap and self-contained.
- **AFINI-T (2019-2022):** strong papers, but no product or spin-out found (unverified). **Lesson:** research accuracy does not equal workflow adoption.
- **FlavoriaFlex:** 23% of trays never got an after-image ([AHFE 2026](https://openaccess.cms-conferences.org/publications/book/978-1-964867-87-8/article/978-1-964867-87-8_2)). **Lesson:** capture at a choke point (dish return or tray cart), not at the bedside.
- **FoodIntech:** a single RGB view failed on containers, purées and yogurt ([MDPI](https://www.mdpi.com/2072-6643/14/1/221)). **Lesson:** depth matters.
- **Meal Vision:** loud launch in 2023, no public scale-up news since (unverified). Possible limit: it depends on special RFID plates and AWS (speculation).
- **Consumer plates (Fitly SmartPlate):** Shark Tank flop, no working prototype ([SlashGear](https://www.slashgear.com/1357306/what-happened-smartplate-shark-tank-season-7)). **Lesson:** hardware that changes the plate is hard to sell.

### (c) White space for Intake.ai (honest)
- **US LTC is open.** No shipping camera intake product was found there. Meal Vision is in Australia, Nuvilab is US hospital-first, and foodintech is in France.
  - Say "**we found no US LTC product**", not "**first ever**".
- **Join to the US tray ticket (QR).** MealTracker, MealSuite and CBORD already print tickets, so no special plates are needed, unlike Meal Vision's RFID plates.
- **On-site edge processing.** Images stay in the building, and only numbers leave. Meal Vision is AWS-based. Nuvilab is cloud (unverified). This fits HIPAA comfort and patchy facility Wi-Fi, the SOMPO pain point.
- **Protein-first streak alerts tied to the care plan,** not just a waste dashboard.
- **Open accuracy method:** a 1 g scale ground truth, reported per food class, including texture-modified food. Almost no vendor publishes this. Research papers do, and that is the bar to match.
- **Roboflow angle:** this is a fine-tune-plus-workflow problem (segment → depth → join → alert) that any facility can retrain on its own menu. Not a bespoke research rig.
- **Do NOT claim:** better accuracy than Nuvilab or AFINI-T (no head-to-head), being first to use depth, or replacing the RD.

### (d) Likely panel questions and short answers
1. **"Isn't this already done? Meal Vision, Nuvilab?"**
   - Yes, the idea is proven. That de-risks it.
   - Meal Vision: Australian, cloud, RFID plates, no published accuracy.
   - Nuvilab: hospital-first, still validating intake.
   - My PoC shows the US LTC version on edge, built on Roboflow in days.
2. **"Why depth? Isn't RGB enough?"**
   - Area is not volume.
   - Waterloo named it "visual-volume discordance". FoodIntech failed on bowls and purées. Nutrition5k cut mass error from 18.7% to 13.7% with depth.
3. **"How accurate are you?"**
   - Give the measured number, against a 1 g scale, per class.
   - Benchmarks: AFINI-T -0.4 ± 36.7 mL; hospital pilots ≈10% MAE; staff about 20 pts too high.
4. **"Why not just weigh the tray?"**
   - A scale gives total grams only. It cannot tell protein from potatoes.
   - Per-item intake is the clinical value. The scale stays in as ground truth.
5. **"Who pays?"**
   - The operator (DON/RD budget). Value comes from fewer F692 citations, fewer weight-loss QM hits, and CNA minutes saved.
   - Or the contract caterer (Compass/Morrison model).
   - Admit that payer ROI is not yet proven.
6. **"Why edge?"**
   - PHI (resident faces and names on tickets) stays local.
   - It works when Wi-Fi drops.
   - The box costs $249.
7. **"What about puréed or texture-modified diets?"**
   - This is the known failure (SOMPO/NEC, FoodIntech).
   - Depth helps. Flag it as a v2 data-collection target.
8. **"Incumbent EHRs will just add this."**
   - They have no camera footprint at the dish return.
   - Likely path: integrate (an API into PCC or MealTracker) or get acquired.

### (e) Risks
- **Incumbents and fast followers:**
  - Nuvilab already has hardware, depth, a Morrison channel and a stated LTC plan.
  - Compass could bring Meal Vision to the US through Morrison or Crothall (speculation).
  - Winnow/Leanpath or Mashgin could add after-scans.
- **Buyer budget:**
  - US SNFs run on thin Medicaid margins.
  - The staffing mandate repeal removes one forcing function.
  - The ROI must be in CNA minutes or survey-risk terms.
- **Integration:**
  - Tray ticket formats differ by vendor.
  - Writing intake into PCC needs a partner API. Without it, staff double-chart.
- **Workflow:** trays that never come back (23% at Turku), shared plates, food moved between plates, family-brought food.
- **Accuracy edge cases:** soups, purées, drinks, occlusion (lids, wrappers), piled food.
- **Regulatory:** if outputs drive clinical decisions, there may be FDA CDS/SaMD questions (unverified). HIPAA covers images of residents' faces and tickets.
- **Supply:** the PoC uses an Orbbec DaBai DCW on legacy OpenNI; depth-camera market is shifting (RealSense spin-out), so pick a supported RGB-D SKU for any pilot.
