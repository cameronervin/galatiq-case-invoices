import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";

describe("decoder module boundaries", () => {
  it("keeps each decoder implementation focused", () => {
    const directory = __dirname;
    const sourceFiles = readdirSync(directory).filter(
      (name) => name.endsWith(".ts") && !name.endsWith(".test.ts")
    );

    for (const sourceFile of sourceFiles) {
      const lineCount = readFileSync(join(directory, sourceFile), "utf8").split("\n").length;
      expect({ sourceFile, lineCount }).toEqual({
        sourceFile,
        lineCount: expect.any(Number)
      });
      expect(lineCount).toBeLessThanOrEqual(120);
    }
  });

  it("keeps the stable run decoder entrypoint export-only", () => {
    const entrypoint = readFileSync(join(__dirname, "..", "runDecoders.ts"), "utf8");

    expect(entrypoint).not.toMatch(/function|const|class/);
  });
});
