import { FileBlob, PresentationFile } from "@oai/artifact-tool";

const deck = await PresentationFile.importPptx(
  await FileBlob.load("/Users/samsonkitigo/Documents/Codex/sportshub/tmp/presentation-revision-jwytUc/template-starter.pptx"),
);

for (const [slideIndex, slide] of deck.slides.items.entries()) {
  console.log(`SLIDE ${slideIndex + 1}`);
  for (const [shapeIndex, shape] of slide.shapes.items.entries()) {
    const text = shape.text?.toString?.() ?? shape.text ?? "";
    const p = shape.position ?? shape.frame ?? {};
    console.log(shapeIndex, shape.id, JSON.stringify(text), JSON.stringify(p));
  }
}

console.log("STYLE", deck.slides.items[2].shapes.items[1].text.style);
console.log("FILL", deck.slides.items[4].shapes.items[7].fill);
console.log("TEXT_KEYS", Object.keys(deck.slides.items[2].shapes.items[7].text));
console.log("TEXT_PROTO", deck.slides.items[2].shapes.items[7].text.toProto?.());
