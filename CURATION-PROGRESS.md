# MIC Nutrient Curation Progress

Track curation status for each nutrient entry from the Linus Pauling Institute MIC website.

**Legend:**
- [ ] Not started
- [x] Completed
- [~] In progress (use `[ ]` in markdown, add note)

---

## Vitamins

- [x] Vitamin C (`kb/nutrients/vitamins/vitamin-c.yaml`)
- [x] Biotin (`kb/nutrients/vitamins/biotin.yaml`)
- [X] Folate (`kb/nutrients/vitamins/folate.yaml`)
- [x] Niacin (`kb/nutrients/vitamins/niacin.yaml`)
- [x] Pantothenic Acid (`kb/nutrients/vitamins/pantothenic-acid.yaml`)
- [x] Riboflavin (`kb/nutrients/vitamins/riboflavin.yaml`)
- [x] Thiamin (`kb/nutrients/vitamins/thiamin.yaml`)
- [x] Vitamin A (`kb/nutrients/vitamins/vitamin-a.yaml`)
- [x] Vitamin B6 (`kb/nutrients/vitamins/vitamin-b6.yaml`)
- [x] Vitamin B12 (`kb/nutrients/vitamins/vitamin-b12.yaml`)
- [x] Vitamin D (`kb/nutrients/vitamins/vitamin-d.yaml`)
- [x] Vitamin E (`kb/nutrients/vitamins/vitamin-e.yaml`)
- [x] Vitamin K (`kb/nutrients/vitamins/vitamin-k.yaml`)

## Minerals

- [x] Calcium (`kb/nutrients/minerals/calcium.yaml`)
- [x] Chromium (`kb/nutrients/minerals/chromium.yaml`)
- [x] Copper (`kb/nutrients/minerals/copper.yaml`)
- [x] Fluoride (`kb/nutrients/minerals/fluoride.yaml`)
- [x] Iodine (`kb/nutrients/minerals/iodine.yaml`)
- [x] Iron (`kb/nutrients/minerals/iron.yaml`)
- [x] Magnesium (`kb/nutrients/minerals/magnesium.yaml`)
- [x] Manganese (`kb/nutrients/minerals/manganese.yaml`)
- [x] Molybdenum (`kb/nutrients/minerals/molybdenum.yaml`)
- [x] Phosphorus (`kb/nutrients/minerals/phosphorus.yaml`)
- [x] Potassium (`kb/nutrients/minerals/potassium.yaml`)
- [x] Selenium (`kb/nutrients/minerals/selenium.yaml`)
- [x] Sodium (`kb/nutrients/minerals/sodium.yaml`)
- [x] Zinc (`kb/nutrients/minerals/zinc.yaml`)

## Other Nutrients

- [x] Choline (`kb/nutrients/vitamins/choline.yaml`)
- [x] Essential Fatty Acids (`kb/nutrients/dietary-factors/essential-fatty-acids.yaml`)
- [x] Fiber (`kb/nutrients/dietary-factors/fiber.yaml`)

## Dietary Factors

- [x] L-Carnitine (`kb/nutrients/dietary-factors/l-carnitine.yaml`)
- [x] Coenzyme Q10 (`kb/nutrients/dietary-factors/coenzyme-q10.yaml`)
- [x] Lipoic Acid (`kb/nutrients/dietary-factors/lipoic-acid.yaml`)

### Phytochemicals

- [x] Carotenoids (`kb/nutrients/dietary-factors/carotenoids.yaml`)
- [x] Chlorophyll (`kb/nutrients/dietary-factors/chlorophyll.yaml`)
- [x] Curcumin (`kb/nutrients/dietary-factors/curcumin.yaml`)
- [x] Flavonoids (`kb/nutrients/dietary-factors/flavonoids.yaml`)
- [x] Garlic (phytochemical) (`kb/nutrients/dietary-factors/garlic-phytochemical.yaml`)
- [x] Indole-3-Carbinol (`kb/nutrients/dietary-factors/indole-3-carbinol.yaml`)
- [x] Isothiocyanates (`kb/nutrients/dietary-factors/isothiocyanates.yaml`)
- [x] Lignans (`kb/nutrients/dietary-factors/lignans.yaml`)
- [x] Phytosterols (`kb/nutrients/dietary-factors/phytosterols.yaml`)
- [x] Resveratrol (`kb/nutrients/dietary-factors/resveratrol.yaml`)
- [x] Soy Isoflavones (`kb/nutrients/dietary-factors/soy-isoflavones.yaml`)

## Food and Beverages

- [x] Fruit and Vegetables (`kb/nutrients/food-beverages/fruit-vegetables.yaml`)
- [x] Cruciferous Vegetables (`kb/nutrients/food-beverages/cruciferous-vegetables.yaml`)
- [x] Garlic (`kb/nutrients/food-beverages/garlic.yaml`)
- [x] Legumes (`kb/nutrients/food-beverages/legumes.yaml`)
- [x] Nuts (`kb/nutrients/food-beverages/nuts.yaml`)
- [x] Whole Grains (`kb/nutrients/food-beverages/whole-grains.yaml`)
- [x] Coffee (`kb/nutrients/food-beverages/coffee.yaml`)
- [x] Tea (`kb/nutrients/food-beverages/tea.yaml`)
- [x] Alcoholic Beverages (`kb/nutrients/food-beverages/alcoholic-beverages.yaml`)
- [x] Glycemic Index/Load (`kb/nutrients/food-beverages/glycemic-index-glycemic-load.yaml`)

---

## Summary

| Category | Total | Completed | Remaining |
|----------|-------|-----------|-----------|
| Vitamins | 13 | 13 | 0 |
| Minerals | 14 | 14 | 0 |
| Other Nutrients | 3 | 3 | 0 |
| Dietary Factors | 14 | 14 | 0 |
| Food & Beverages | 10 | 10 | 0 |
| **Total** | **54** | **54** | **0** |

---

## Notes

- Run `just validate kb/nutrients/<category>/<nutrient>.yaml` after completing each entry
- Run `just validate-terms` to check ontology term validity
- Run `just validate-references` to verify evidence snippets match PubMed abstracts
