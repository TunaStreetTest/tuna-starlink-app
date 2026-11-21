export type FaultKind = "missing" | "dead";

export function faultCard(kind: FaultKind, token: string): string[] {
  const name = (token || "unnamed").slice(0, 24);
  if (kind === "dead") {
    return [
      "FRAME DROPPED",
      "",
      "dish had the channel.",
      "picture left the bird.",
      "",
      name,
      "glass still dark.",
    ];
  }
  return [
    "NO CARRIER",
    "",
    "dish open.  wire quiet.",
    "this plate never left the bird.",
    "",
    name,
    "not on this link.",
  ];
}

export function faultPage(kind: FaultKind, token: string): { kicker: string; headline: string; caption: string } {
  if (kind === "dead") {
    return {
      kicker: "Frame dropped",
      headline: "The picture fell off the bird",
      caption: [
        token ? `${token} is a real channel. The frame is not.` : "The channel is real. The frame is not.",
        "",
        "The dish held the Starlink link.",
        "The plate was named. The picture never arrived.",
        "Snow is the only frame left on the glass.",
      ].join("\n"),
    };
  }
  return {
    kicker: "No carrier",
    headline: "The dish came back empty",
    caption: [
      token ? `${token} is not a plate on this link.` : "This address is not a plate on this link.",
      "",
      "Bird in view. Wire up. Nothing came down.",
      "Starlink held the pass. The studio sent snow.",
    ].join("\n"),
  };
}
