export async function loadCalculator(wasmPath) {
  const bytes = await globalThis.fetch(wasmPath).then((response) => response.arrayBuffer());
  const { instance } = await WebAssembly.instantiate(bytes, {});
  return instance.exports;
}
