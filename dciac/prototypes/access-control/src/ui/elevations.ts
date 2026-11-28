import { state } from "../state";
import { esc } from "./format";

export const ELEVATION_STEPS = [
  { id: "site", label: "Outside", hint: "Yard and shell" },
  { id: "hall", label: "Hall", hint: "Compute halls" },
  { id: "pod", label: "Pod", hint: "Aisles and rows" },
  { id: "row", label: "Row", hint: "Fronts and rears" },
  { id: "rack", label: "Rack", hint: "U-space elevation" },
  { id: "server", label: "Device", hint: "Inlet and exhaust" },
];

export function elevationFromLevel(level) {
  if (level === "part") return "server";
  if (level === "feed") return state.floor.podId ? "pod" : "site";
  if (ELEVATION_STEPS.some((step) => step.id === level)) return level;
  return "hall";
}

export function elevationIndex(level) {
  const id = elevationFromLevel(level);
  const index = ELEVATION_STEPS.findIndex((step) => step.id === id);
  return index < 0 ? 1 : index;
}

export function faceSwitchHtml() {
  const rear = state.floor.face === "rear";
  return '<div class="face-switch" role="group" aria-label="Rack elevation face">' +
    '<button type="button" data-act="rack-face" data-face="front"' + (rear ? "" : ' aria-pressed="true"') +
    ">Cold aisle front</button>" +
    '<button type="button" data-act="rack-face" data-face="rear"' + (rear ? ' aria-pressed="true"' : "") +
    ">Hot aisle rear</button></div>";
}

export function elevationNavHtml(opts?: { face?: boolean }) {
  const current = elevationFromLevel(state.floor.level);
  const index = elevationIndex(state.floor.level);
  const steps = ELEVATION_STEPS.map((step, i) => {
    const currentAttr = step.id === current ? ' aria-current="step"' : "";
    const reached = i <= index ? " reached" : "";
    return '<li><button type="button" class="elevation-step' + reached + '" data-act="floor-elevation" data-level="' +
      step.id + '"' + currentAttr + ' title="' + esc(step.hint) + '"><b>' + (i + 1) + "</b><span>" +
      esc(step.label) + "</span></button></li>";
  }).join("");
  const showFace = opts && opts.face;
  return '<nav class="elevation-nav" aria-label="Elevation views">' +
    '<button type="button" class="elevation-nudge" data-act="floor-step" data-dir="-1" aria-label="Previous elevation"' +
    (index <= 0 ? " disabled" : "") + ">‹</button>" +
    '<ol>' + steps + "</ol>" +
    '<button type="button" class="elevation-nudge" data-act="floor-step" data-dir="1" aria-label="Next elevation"' +
    (index >= ELEVATION_STEPS.length - 1 ? " disabled" : "") + ">›</button>" +
    (showFace ? faceSwitchHtml() : "") +
    "</nav>";
}
