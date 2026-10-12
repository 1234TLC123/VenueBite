import { runParcelTests } from "./parcel-layer.test.mjs";
import { runOccupancyStateTests } from "./occupancy-state.test.mjs";
import { runFormUITests } from "./form-ui.test.mjs";
import { runSavedSiteTests } from "./saved-sites.test.mjs";
import { runRegulatoryStateTests } from "./regulatory-state.test.mjs";

export async function runAllJavaScriptTests() {
  const suites = {
    parcel: runParcelTests(),
    occupancy: await runOccupancyStateTests(),
    form: runFormUITests(),
    saved: runSavedSiteTests(),
    regulatory: await runRegulatoryStateTests(),
  };
  return { passed: Object.values(suites).reduce((total, cases) => total + cases.length, 0), suites };
}

console.log(JSON.stringify(await runAllJavaScriptTests(), null, 2));
