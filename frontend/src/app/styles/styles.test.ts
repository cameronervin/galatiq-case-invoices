import { readFileSync } from "node:fs";
import { join } from "node:path";

const appStylesRoot = join(process.cwd(), "src", "app");
const stylesheetImports = [
  '@import "tailwindcss";',
  '@import "./styles/foundations.css";',
  '@import "./styles/controls-upload.css";',
  '@import "./styles/runs.css";',
  '@import "./styles/details.css";',
  '@import "./styles/invoice-findings.css";',
  '@import "./styles/review-timeline.css";',
  '@import "./styles/responsive.css";'
];

describe("global stylesheet architecture", () => {
  it("keeps the global entrypoint as an ordered import manifest", () => {
    const entrypoint = readFileSync(join(appStylesRoot, "globals.css"), "utf8");

    expect(entrypoint.trim().split("\n")).toEqual(stylesheetImports);
  });

  it("keeps responsibility-focused stylesheets below 200 lines", () => {
    for (const importRule of stylesheetImports.slice(1)) {
      const relativePath = importRule.match(/"(.+)"/)?.[1];
      expect(relativePath).toBeDefined();

      const stylesheet = readFileSync(join(appStylesRoot, relativePath!), "utf8");
      expect(stylesheet.trim().length).toBeGreaterThan(0);
      expect(stylesheet.trimEnd().split("\n").length).toBeLessThan(200);
    }
  });
});
