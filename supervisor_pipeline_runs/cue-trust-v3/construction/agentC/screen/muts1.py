import json
F = "source/org/jfree/data/general/DatasetUtilities.java"
ITD_HEAD = "        double maximum = Double.NEGATIVE_INFINITY;\n\n        if (includeInterval && dataset instanceof IntervalXYDataset) {\n            // handle special case of IntervalXYDataset\n            IntervalXYDataset ixyd"
m = [
 {"id": "ITD-max-init-0", "file": F, "old": ITD_HEAD, "new": ITD_HEAD.replace("Double.NEGATIVE_INFINITY", "0", 1)},
 {"id": "ITD-max-init-MIN_VALUE", "file": F, "old": ITD_HEAD, "new": ITD_HEAD.replace("Double.NEGATIVE_INFINITY", "Double.MIN_VALUE", 1)},
 {"id": "ITD-branch-negate-flag", "file": F, "old": ITD_HEAD, "new": ITD_HEAD.replace("if (includeInterval &&", "if (!includeInterval &&", 1)},
 {"id": "ITD-uvalue-start", "file": F, "old": "double uvalue = ixyd.getEndXValue(series, item);", "new": "double uvalue = ixyd.getStartXValue(series, item);"},
 {"id": "ITD-plain-max-from-min", "file": F, "old": "                    double x = dataset.getXValue(series, item);\n                    if (!Double.isNaN(x)) {\n                        minimum = Math.min(minimum, x);\n                        maximum = Math.max(maximum, x);",
  "new": "                    double x = dataset.getXValue(series, item);\n                    if (!Double.isNaN(x)) {\n                        minimum = Math.min(minimum, x);\n                        maximum = Math.max(minimum, x);"},
 {"id": "ID-uvalue-start", "file": F, "old": "uvalue = intervalXYData.getEndXValue(series, item);", "new": "uvalue = intervalXYData.getStartXValue(series, item);"},
 {"id": "ID-empty-check-ge", "file": F, "old": "        if (minimum > maximum) {\n            return null;\n        }\n        else {\n            return new Range(minimum, maximum);\n        }\n    }\n\n    /**\n     * Returns the range of values in the range for the dataset.",
  "new": "        if (minimum >= maximum) {\n            return null;\n        }\n        else {\n            return new Range(minimum, maximum);\n        }\n    }\n\n    /**\n     * Returns the range of values in the range for the dataset."},
]
json.dump(m, open("screen/muts1.json", "w"), indent=1)
t = open("work/Chart/" + F).read()
for x in m: print(x["id"], t.count(x["old"]))
