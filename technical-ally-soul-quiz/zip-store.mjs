/* Minimal dependency-free ZIP writer. Entries are stored without compression. */

const CRC_TABLE = (() => {
  const table = new Uint32Array(256);
  for (let value = 0; value < 256; value += 1) {
    let crc = value;
    for (let bit = 0; bit < 8; bit += 1) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
    table[value] = crc >>> 0;
  }
  return table;
})();

const encoder = new TextEncoder();

export function crc32(bytes) {
  let crc = 0xffffffff;
  for (const byte of bytes) crc = (crc >>> 8) ^ CRC_TABLE[(crc ^ byte) & 0xff];
  return (crc ^ 0xffffffff) >>> 0;
}

function u16(value) {
  const bytes = new Uint8Array(2);
  new DataView(bytes.buffer).setUint16(0, value, true);
  return bytes;
}

function u32(value) {
  const bytes = new Uint8Array(4);
  new DataView(bytes.buffer).setUint32(0, value >>> 0, true);
  return bytes;
}

function concat(parts) {
  const length = parts.reduce((sum, part) => sum + part.length, 0);
  const output = new Uint8Array(length);
  let offset = 0;
  for (const part of parts) {
    output.set(part, offset);
    offset += part.length;
  }
  return output;
}

function dosDateTime(dateValue) {
  const date = dateValue instanceof Date && !Number.isNaN(dateValue.valueOf()) ? dateValue : new Date();
  const year = Math.max(1980, Math.min(2107, date.getUTCFullYear()));
  const dosTime = ((date.getUTCHours() & 0x1f) << 11) | ((date.getUTCMinutes() & 0x3f) << 5) | ((Math.floor(date.getUTCSeconds() / 2)) & 0x1f);
  const dosDate = (((year - 1980) & 0x7f) << 9) | (((date.getUTCMonth() + 1) & 0x0f) << 5) | (date.getUTCDate() & 0x1f);
  return { dosDate, dosTime };
}

function normalizeEntries(entries) {
  const names = new Set();
  return entries.map((entry) => {
    const name = String(entry.name || '');
    if (!/^[A-Za-z0-9][A-Za-z0-9._/-]{0,159}$/.test(name) || name.includes('..') || name.includes('\\') || name.startsWith('/')) throw new Error('Unsafe ZIP entry name.');
    if (names.has(name.toLowerCase())) throw new Error('Duplicate ZIP entry name.');
    names.add(name.toLowerCase());
    const data = entry.data instanceof Uint8Array ? entry.data : encoder.encode(String(entry.data ?? ''));
    return { name, nameBytes: encoder.encode(name), data, crc: crc32(data) };
  });
}

export function createStoredZip(entries, dateValue = new Date()) {
  const normalized = normalizeEntries(entries);
  const { dosDate, dosTime } = dosDateTime(dateValue);
  const localParts = [];
  const centralParts = [];
  let localOffset = 0;

  for (const entry of normalized) {
    const localHeader = concat([
      u32(0x04034b50), u16(20), u16(0x0800), u16(0), u16(dosTime), u16(dosDate),
      u32(entry.crc), u32(entry.data.length), u32(entry.data.length),
      u16(entry.nameBytes.length), u16(0), entry.nameBytes
    ]);
    localParts.push(localHeader, entry.data);

    const centralHeader = concat([
      u32(0x02014b50), u16(20), u16(20), u16(0x0800), u16(0), u16(dosTime), u16(dosDate),
      u32(entry.crc), u32(entry.data.length), u32(entry.data.length),
      u16(entry.nameBytes.length), u16(0), u16(0), u16(0), u16(0), u32(0), u32(localOffset), entry.nameBytes
    ]);
    centralParts.push(centralHeader);
    localOffset += localHeader.length + entry.data.length;
  }

  const localData = concat(localParts);
  const centralData = concat(centralParts);
  const endRecord = concat([
    u32(0x06054b50), u16(0), u16(0), u16(normalized.length), u16(normalized.length),
    u32(centralData.length), u32(localData.length), u16(0)
  ]);
  return concat([localData, centralData, endRecord]);
}
