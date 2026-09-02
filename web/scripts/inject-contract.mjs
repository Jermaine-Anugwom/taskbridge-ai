import fs from "node:fs";
import path from "node:path";

const outDir = path.resolve("out");
const contract = "<!-- THESIS: Make the automation decision on the workshop table, not inside a black box. OWN-WORLD: Cool paper, cobalt binder tabs, lime review marks, and movable process tiles. STORY: Listen, map, decide, explain, simulate, measure, and hand off. FIRST VIEWPORT: Scenario folders, fixed stage rail, and a full-width before-and-after map. FORM: grounded operations workshop table, seed 3bc2dcef. FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance -->";

function visit(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) visit(target);
    if (entry.isFile() && entry.name.endsWith(".html")) {
      const html = fs.readFileSync(target, "utf8");
      fs.writeFileSync(target, html.replace("<body>", `<body>${contract}`));
    }
  }
}

visit(outDir);
