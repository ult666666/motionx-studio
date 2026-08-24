#!/usr/bin/env node
/**
 * MOTIONX asset-integrity guard.
 *
 * Protects the immutable video masters and verifies the public derivatives,
 * posters, share cards, and source-visible media references used by the site.
 */
import { createHash } from "node:crypto";
import { existsSync, readdirSync, readFileSync, statSync } from "node:fs";
import path from "node:path";
import { spawnSync } from "node:child_process";

const root = process.cwd();
const failures = [];
const skips = [];
let checks = 0;

const immutableAssetRoots = [
  "public/videos",
  "public/posters",
  "public/images",
  "public/captions",
];
const immutableHeaderSources = [
  "/videos/:path*.:hash([0-9a-f]{12}).mp4",
  "/posters/:path*.:hash([0-9a-f]{12}).webp",
  "/images/:path*.:hash([0-9a-f]{12}).webp",
  "/captions/:path*.:hash([0-9a-f]{12}).en.vtt",
];
const immutableCacheControl = "public, max-age=31536000, immutable";

const isCI = /^(1|true)$/i.test(process.env.CI ?? "");

const masterContracts = [
  {
    file: "hf_20260614_040815_e6eb6755-40cb-472a-b5ab-638d325d7934.mp4",
    sha256: "afd5ff1cb6bd7be8e4779faf1cbb595edaeca35b35930b6d1bc8080ee3b82675",
  },
  {
    file: "hf_20260614_040821_b1ca5af0-1e2a-4853-88dd-ee766d34709e (1).mp4",
    sha256: "d9d7be97547a003982e81745e66e7b9815871d4ea1a8938f18861674bb66e037",
  },
  {
    file: "hf_20260714_172122_c7283f1c-769e-4161-81b8-b232ffd78e39.mp4",
    sha256: "29d0400d350d94967eaf0bbaf1860da25c44e69be57a3b67f0ebad87f9fdc63a",
  },
  // FURIA delivery masters (supplied as a package, not Higgsfield-native). The
  // shipped web copy is re-encoded from the 16:9 master with the third-party
  // wordmark removed; these stay byte-immutable so that edit is reproducible.
  {
    file: "furia_16x9_1080p_master.mp4",
    sha256: "4fb190ffea6102a6fb1b61f3a685fc3f38dcc6ba573435057a698803bd323a57",
  },
  {
    file: "furia_9x16_720p_master.mp4",
    sha256: "00b8ebea75b45ec61a26fc6dc6279909f5996a25c8c1d87a33766b6cdd99a132",
  },
];

const videoContracts = [
  {
    file: "public/videos/renewal-botanical.d503303f4c24.mp4",
    width: 1080,
    height: 1920,
    audioCodec: "aac",
    budgetBytes: 16 * 1024 * 1024,
  },
  {
    file: "public/videos/liquid-signal.c24f676131a6.mp4",
    width: 1920,
    height: 1080,
    audioCodec: "aac",
    budgetBytes: 16 * 1024 * 1024,
  },
  {
    file: "public/videos/furia.286ebdadbddd.mp4",
    width: 1920,
    height: 1080,
    audioCodec: "aac",
    budgetBytes: 16 * 1024 * 1024,
  },
  // Agentic Trading is a supplier-prepared web build from the approved asset
  // pack (archive hash recorded in docs/asset-integrity.md), not an archival
  // production master. Pin the incoming web-build bytes so provenance cannot
  // silently drift after promotion.
  {
    file: "public/videos/agentic-trading.344a87357144.mp4",
    width: 1920,
    height: 1080,
    audioCodec: "aac",
    budgetBytes: 16 * 1024 * 1024,
    sha256: "344a87357144360755462484e3978e46d106fac251f11a52d4e62c64dd74801f",
  },
  {
    file: "public/videos/agentic-trading-hero.7dfc19e34a48.mp4",
    width: 1920,
    height: 1080,
    audioCodec: null,
    budgetBytes: 3 * 1024 * 1024,
  },
  // Mobile derivatives — re-encoded from the approved desktop web copies for
  // the <source media> ladder (same edit, same exclusions). Byte ceilings sit
  // ~15-20% above the shipped encodes so a silent quality/bitrate regression
  // fails loudly. `duplicateOf` enforces "derived from, never identical to".
  {
    file: "public/videos/renewal-botanical-mobile.5bbade5a0a0e.mp4",
    width: 720,
    height: 1280,
    audioCodec: "aac",
    budgetBytes: 2_500_000,
    duplicateOf: "public/videos/renewal-botanical.d503303f4c24.mp4",
    durationOf: "public/videos/renewal-botanical.d503303f4c24.mp4",
  },
  {
    file: "public/videos/liquid-signal-mobile.499b4ad7198a.mp4",
    width: 960,
    height: 540,
    audioCodec: "aac",
    budgetBytes: 4_500_000,
    duplicateOf: "public/videos/liquid-signal.c24f676131a6.mp4",
    durationOf: "public/videos/liquid-signal.c24f676131a6.mp4",
  },
  {
    file: "public/videos/furia-mobile.b39c4813f6bb.mp4",
    width: 960,
    height: 540,
    audioCodec: "aac",
    budgetBytes: 5_000_000,
    duplicateOf: "public/videos/furia.286ebdadbddd.mp4",
    durationOf: "public/videos/furia.286ebdadbddd.mp4",
  },
  {
    file: "public/videos/agentic-trading-mobile.4610f3f19a82.mp4",
    width: 960,
    height: 540,
    audioCodec: "aac",
    budgetBytes: 5 * 1024 * 1024,
    duplicateOf: "public/videos/agentic-trading.344a87357144.mp4",
    durationOf: "public/videos/agentic-trading.344a87357144.mp4",
  },
  // Hero-only art direction: the supplied vertical campaign build is the
  // approved source for this purpose-built 9:16 reframe. It shares the exact
  // claim-safe beat timings with the widescreen teaser.
  {
    file: "public/videos/agentic-trading-hero-mobile.971b3f3dde67.mp4",
    width: 720,
    height: 1280,
    audioCodec: null,
    budgetBytes: 1_200_000,
    duplicateOf: "public/videos/agentic-trading-hero.7dfc19e34a48.mp4",
    durationOf: "public/videos/agentic-trading-hero.7dfc19e34a48.mp4",
  },
];

const expectedPublicVideos = videoContracts.map(({ file }) => file);

const captionContracts = [
  { file: "public/captions/renewal-botanical.e611670510fd.en.vtt", video: "public/videos/renewal-botanical.d503303f4c24.mp4" },
  { file: "public/captions/liquid-signal.34ac9c980cef.en.vtt", video: "public/videos/liquid-signal.c24f676131a6.mp4" },
  { file: "public/captions/furia.d7d68405aded.en.vtt", video: "public/videos/furia.286ebdadbddd.mp4" },
  { file: "public/captions/agentic-trading.66d344306cb2.en.vtt", video: "public/videos/agentic-trading.344a87357144.mp4" },
];

const expectedPosters = [
  "public/posters/renewal.2f7a5aad01b8.webp",
  "public/posters/liquid-signal.cdfb416c6c9d.webp",
  "public/posters/furia.ed1339cb90bc.webp",
  "public/posters/agentic-trading.e09753d24951.webp",
  "public/posters/agentic-trading-hero.2b41aa4ef05c.webp",
  "public/posters/agentic-trading-hero-mobile.850d5c58d577.webp",
];

// Project-specific still artwork is intentionally separate from video posters:
// these are editorial frames rendered below the fold with responsive sources.
// The Agentic hero poster is included here as well because its claim-safe crop
// (no numeric score or baked player timeline) is a load-bearing content rule.
const imageContracts = [
  {
    file: "public/posters/agentic-trading-hero.2b41aa4ef05c.webp",
    width: 1920,
    height: 1080,
    budgetBytes: 250 * 1024,
  },
  {
    file: "public/posters/agentic-trading-hero-mobile.850d5c58d577.webp",
    width: 1080,
    height: 1920,
    budgetBytes: 120 * 1024,
  },
  {
    file: "public/images/work/agentic-trading/strategy-board-1920.79064a62aeea.webp",
    width: 1920,
    height: 815,
    budgetBytes: 300 * 1024,
  },
  {
    file: "public/images/work/agentic-trading/strategy-board-960.70da7ef150bb.webp",
    width: 960,
    height: 407,
    budgetBytes: 120 * 1024,
  },
];

// Every promoted Agentic asset is immutable once approved for publication.
// Structural media checks catch format/stream regressions; these fingerprints
// additionally prevent a visually different file from silently retaining the
// same path, dimensions, duration, and byte budget.
const promotedAgenticFingerprints = [
  {
    file: "public/videos/agentic-trading-hero.7dfc19e34a48.mp4",
    sha256: "7dfc19e34a48963ad60be57d9e2818569ad912dcacfb89fa8c8811dd3faebc45",
  },
  {
    file: "public/videos/agentic-trading-mobile.4610f3f19a82.mp4",
    sha256: "4610f3f19a8239101a0894c0a55cbdd5a97fc4e922980350f68817471072c309",
  },
  {
    file: "public/videos/agentic-trading-hero-mobile.971b3f3dde67.mp4",
    sha256: "971b3f3dde67304ffeb884fad920817daad408fabf77afe747ca43f38a493a4a",
  },
  {
    file: "public/posters/agentic-trading.e09753d24951.webp",
    sha256: "e09753d249516484a1669414795020cce2f14174a6e3b622dc62ab4055195070",
  },
  {
    file: "public/posters/agentic-trading-hero.2b41aa4ef05c.webp",
    sha256: "2b41aa4ef05c206b14ff06180fd9b85c6909f8061ccc18cbce67a16479039c8d",
  },
  {
    file: "public/posters/agentic-trading-hero-mobile.850d5c58d577.webp",
    sha256: "850d5c58d57774fa75651a9a2b42fdce223a718310e3441f35c6eeb13b6d8135",
  },
  {
    file: "public/images/work/agentic-trading/strategy-board-1920.79064a62aeea.webp",
    sha256: "79064a62aeea146ed83af21b94ab2ac35d63eedcc4e72c71c75fc76187a83cf7",
  },
  {
    file: "public/images/work/agentic-trading/strategy-board-960.70da7ef150bb.webp",
    sha256: "70da7ef150bb13160302b013bf2486c7bd0e9de75d868608047f4a882aec79a5",
  },
  {
    file: "public/og/agentic-trading.jpg",
    sha256: "2f3dafaf33d99445c14f29ecf3f67bea9d62c588bb84832a7b66d7c8042afb82",
  },
  {
    file: "public/captions/agentic-trading.66d344306cb2.en.vtt",
    sha256: "66d344306cb255d80169082fefd990df780a4aa925663cf72a121e87dc68c170",
  },
];

const expectedArtwork = imageContracts
  .map(({ file }) => file)
  .filter((file) => !expectedPosters.includes(file));

const expectedOgCards = [
  "public/og/og-image.jpg",
  "public/og/renewal.jpg",
  "public/og/liquid-signal.jpg",
  "public/og/furia.jpg",
  "public/og/agentic-trading.jpg",
  "public/og/system-study.jpg",
];

function check(condition, message) {
  checks += 1;
  if (!condition) failures.push(message);
}

function absolute(file) {
  return path.join(root, file);
}

function read(file) {
  return readFileSync(absolute(file), "utf8");
}

function exists(file) {
  return existsSync(absolute(file));
}

function size(file) {
  return statSync(absolute(file)).size;
}

function sha256(file) {
  return createHash("sha256").update(readFileSync(absolute(file))).digest("hex");
}

function walk(dir) {
  const abs = absolute(dir);
  return readdirSync(abs, { withFileTypes: true }).flatMap((entry) => {
    const rel = path.join(dir, entry.name);
    if (entry.isDirectory()) return walk(rel);
    return /\.(ts|tsx|mjs|md)$/.test(entry.name) ? [rel] : [];
  });
}

function walkAssets(dir) {
  return readdirSync(absolute(dir), { withFileTypes: true }).flatMap((entry) => {
    const rel = path.join(dir, entry.name);
    return entry.isDirectory() ? walkAssets(rel) : [rel];
  });
}

function discoverFfprobe() {
  const names = process.platform === "win32" ? ["ffprobe.exe", "ffprobe"] : ["ffprobe"];
  const pathCandidates = (process.env.PATH ?? "")
    .split(path.delimiter)
    .filter(Boolean)
    .flatMap((directory) => names.map((name) => path.join(directory, name)));
  const candidates = [
    ...pathCandidates,
    "/opt/anaconda3/envs/motionx/bin/ffprobe",
  ];

  for (const candidate of [...new Set(candidates)]) {
    if (!existsSync(candidate)) continue;
    const result = spawnSync(candidate, ["-version"], {
      encoding: "utf8",
      stdio: ["ignore", "ignore", "ignore"],
    });
    if (!result.error && result.status === 0) return candidate;
  }

  return null;
}

function probeDuration(ffprobe, file) {
  const result = spawnSync(
    ffprobe,
    ["-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", absolute(file)],
    { encoding: "utf8", maxBuffer: 1024 * 1024 },
  );
  if (result.error || result.status !== 0) return null;
  const parsed = Number.parseFloat(result.stdout.trim());
  return Number.isFinite(parsed) ? parsed : null;
}

function probeMedia(ffprobe, file) {
  const result = spawnSync(
    ffprobe,
    [
      "-v",
      "error",
      "-show_entries",
      "stream=codec_type,codec_name,profile,pix_fmt,width,height",
      "-of",
      "json",
      absolute(file),
    ],
    { encoding: "utf8", maxBuffer: 1024 * 1024 },
  );

  if (result.error || result.status !== 0) {
    check(
      false,
      `${file} could not be inspected with ffprobe: ${
        result.error?.message ?? (result.stderr?.trim() || `exit ${result.status}`)
      }`,
    );
    return null;
  }

  try {
    const parsed = JSON.parse(result.stdout);
    check(Array.isArray(parsed.streams), `${file} returned invalid ffprobe stream data.`);
    return Array.isArray(parsed.streams) ? parsed.streams : null;
  } catch (error) {
    check(false, `${file} returned invalid ffprobe JSON: ${error.message}`);
    return null;
  }
}

function topLevelMp4Atoms(file) {
  const buffer = readFileSync(absolute(file));
  const atoms = [];
  let offset = 0;

  while (offset < buffer.length) {
    if (offset + 8 > buffer.length) {
      throw new Error(`truncated atom header at byte ${offset}`);
    }

    const size32 = buffer.readUInt32BE(offset);
    const type = buffer.toString("ascii", offset + 4, offset + 8);
    let atomSize = size32;
    let headerSize = 8;

    if (size32 === 1) {
      if (offset + 16 > buffer.length) {
        throw new Error(`truncated extended atom header at byte ${offset}`);
      }
      const extendedSize = buffer.readBigUInt64BE(offset + 8);
      if (extendedSize > BigInt(Number.MAX_SAFE_INTEGER)) {
        throw new Error(`atom ${type} is too large to inspect safely`);
      }
      atomSize = Number(extendedSize);
      headerSize = 16;
    } else if (size32 === 0) {
      atomSize = buffer.length - offset;
    }

    if (atomSize < headerSize || offset + atomSize > buffer.length) {
      throw new Error(`invalid ${type} atom size ${atomSize} at byte ${offset}`);
    }

    atoms.push(type);
    offset += atomSize;
  }

  return atoms;
}

function jpegDimensions(file) {
  const buffer = readFileSync(absolute(file));
  const hasStartOfImage = buffer.length >= 4 && buffer[0] === 0xff && buffer[1] === 0xd8;
  const hasEndOfImage =
    buffer.length >= 4 && buffer[buffer.length - 2] === 0xff && buffer[buffer.length - 1] === 0xd9;
  if (!hasStartOfImage || !hasEndOfImage) return null;

  const startOfFrameMarkers = new Set([
    0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7,
    0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf,
  ]);
  let offset = 2;

  while (offset < buffer.length) {
    while (offset < buffer.length && buffer[offset] === 0xff) offset += 1;
    if (offset >= buffer.length) break;

    const marker = buffer[offset];
    offset += 1;

    if (marker === 0xd9 || marker === 0xda) break;
    if (marker === 0x01 || (marker >= 0xd0 && marker <= 0xd7)) continue;
    if (offset + 2 > buffer.length) return null;

    const segmentLength = buffer.readUInt16BE(offset);
    if (segmentLength < 2 || offset + segmentLength > buffer.length) return null;

    if (startOfFrameMarkers.has(marker)) {
      if (segmentLength < 7) return null;
      return {
        height: buffer.readUInt16BE(offset + 3),
        width: buffer.readUInt16BE(offset + 5),
      };
    }

    offset += segmentLength;
  }

  return null;
}

for (const contract of masterContracts) {
  if (!exists(contract.file)) {
    if (isCI) {
      skips.push(`${contract.file} (gitignored local master unavailable in CI)`);
    } else {
      check(false, `Original master is missing: ${contract.file}`);
    }
    continue;
  }

  check(
    sha256(contract.file) === contract.sha256,
    `Original master fingerprint changed: ${contract.file}. The immutable master may have been overwritten or recompressed.`,
  );
}

// Versioned files in these roots receive a one-year immutable browser/CDN
// policy. Make that safe by requiring every URL to carry the first 12
// characters of its file hash and by rejecting stale names if bytes are ever replaced.
for (const directory of immutableAssetRoots) {
  for (const file of walkAssets(directory)) {
    const hashInName = path.basename(file).match(/\.([0-9a-f]{12})(?:\.[a-z]{2})?\.[^.]+$/);
    check(Boolean(hashInName), `${file} must include a 12-character SHA-256 content hash.`);
    if (hashInName) {
      check(
        sha256(file).startsWith(hashInName[1]),
        `${file} content no longer matches the hash in its immutable URL. Publish it under a new hash-suffixed filename.`,
      );
    }
  }
}

try {
  const vercelConfig = JSON.parse(read("vercel.json"));
  const headerRules = Array.isArray(vercelConfig.headers) ? vercelConfig.headers : [];
  for (const source of immutableHeaderSources) {
    const rule = headerRules.find(({ source: candidate }) => candidate === source);
    const cacheHeader = rule?.headers?.find(
      ({ key }) => key.toLowerCase() === "cache-control",
    );
    check(
      cacheHeader?.value === immutableCacheControl,
      `vercel.json must set ${immutableCacheControl} for ${source}.`,
    );
  }

  const unexpectedImmutableRules = headerRules.filter((rule) =>
    rule.headers?.some(
      ({ key, value }) =>
        key.toLowerCase() === "cache-control" &&
        /\bimmutable\b/.test(value) &&
        !immutableHeaderSources.includes(rule.source),
    ),
  );
  check(
    unexpectedImmutableRules.length === 0,
    `Immutable caching must stay limited to versioned media roots; found: ${unexpectedImmutableRules
      .map(({ source }) => source)
      .join(", ")}.`,
  );
} catch (error) {
  check(false, `vercel.json could not be validated: ${error.message}`);
}

for (const file of [
  ...expectedPublicVideos,
  ...expectedPosters,
  ...expectedArtwork,
  ...expectedOgCards,
]) {
  check(exists(file), `Expected public asset is missing: ${file}`);
}

for (const contract of promotedAgenticFingerprints) {
  check(exists(contract.file), `Promoted Agentic asset is missing: ${contract.file}`);
  if (!exists(contract.file)) continue;
  check(
    sha256(contract.file) === contract.sha256,
    `Promoted Agentic asset fingerprint changed: ${contract.file}. Re-review the replacement before publishing it.`,
  );
}

for (const file of walk("src")) {
  const text = read(file);
  check(
    !/hf_2026[^"')\n]*\.mp4/i.test(text),
    `${file} must not reference original hf_2026 master videos in public UI.`,
  );

  for (const match of text.matchAll(/["']\/(videos|posters|og|images|captions)\/([^"']+)["']/g)) {
    const rel = `public/${match[1]}/${match[2]}`;
    check(exists(rel), `${file} references missing asset: /${match[1]}/${match[2]}`);
  }
}

const masterFingerprints = new Set(masterContracts.map(({ sha256: hash }) => hash));
for (const file of expectedPublicVideos) {
  if (!exists(file)) continue;
  check(
    !masterFingerprints.has(sha256(file)),
    `${file} is byte-identical to an immutable master; public videos must be re-encoded derivatives.`,
  );
}

const ffprobe = discoverFfprobe();
check(
  Boolean(ffprobe),
  "ffprobe is required for media-contract validation but was not found on PATH or at /opt/anaconda3/envs/motionx/bin/ffprobe. Install FFmpeg and rerun npm run assets:check.",
);

if (ffprobe) {
  for (const contract of videoContracts) {
    if (!exists(contract.file)) continue;
    const streams = probeMedia(ffprobe, contract.file);
    if (!streams) continue;

    const videoStreams = streams.filter(({ codec_type: type }) => type === "video");
    const audioStreams = streams.filter(({ codec_type: type }) => type === "audio");
    check(videoStreams.length === 1, `${contract.file} must contain exactly one video stream.`);

    const video = videoStreams[0];
    if (video) {
      check(video.codec_name === "h264", `${contract.file} video codec must be H.264.`);
      check(video.profile === "High", `${contract.file} H.264 profile must be High.`);
      check(video.pix_fmt === "yuv420p", `${contract.file} pixel format must be yuv420p.`);
      check(
        video.width === contract.width && video.height === contract.height,
        `${contract.file} dimensions must be ${contract.width}x${contract.height}; found ${video.width}x${video.height}.`,
      );
    }

    if (contract.audioCodec === null) {
      check(audioStreams.length === 0, `${contract.file} must not contain an audio stream.`);
    } else {
      check(audioStreams.length === 1, `${contract.file} must contain exactly one audio stream.`);
      if (audioStreams[0]) {
        check(
          audioStreams[0].codec_name === contract.audioCodec,
          `${contract.file} audio codec must be ${contract.audioCodec.toUpperCase()}.`,
        );
      }
    }
  }

  for (const contract of imageContracts) {
    if (!exists(contract.file)) continue;
    const streams = probeMedia(ffprobe, contract.file);
    if (!streams) continue;

    const imageStreams = streams.filter(({ codec_type: type }) => type === "video");
    check(imageStreams.length === 1, `${contract.file} must contain exactly one image stream.`);

    const image = imageStreams[0];
    if (image) {
      check(image.codec_name === "webp", `${contract.file} codec must be WebP.`);
      check(
        image.width === contract.width && image.height === contract.height,
        `${contract.file} dimensions must be ${contract.width}x${contract.height}; found ${image.width}x${image.height}.`,
      );
    }
  }
}

for (const contract of videoContracts) {
  if (!exists(contract.file)) continue;
  if (contract.sha256) {
    check(
      sha256(contract.file) === contract.sha256,
      `${contract.file} no longer matches the promoted supplier web-build fingerprint.`,
    );
  }
  check(
    size(contract.file) <= contract.budgetBytes,
    `${contract.file} exceeds its ${contract.budgetBytes / 1024 / 1024} MiB budget documented in docs/asset-integrity.md.`,
  );

  try {
    const atoms = topLevelMp4Atoms(contract.file);
    const moov = atoms.indexOf("moov");
    const mdat = atoms.indexOf("mdat");
    check(moov >= 0, `${contract.file} is missing a top-level moov atom.`);
    check(mdat >= 0, `${contract.file} is missing a top-level mdat atom.`);
    if (moov >= 0 && mdat >= 0) {
      check(moov < mdat, `${contract.file} is not faststart: moov must appear before mdat.`);
    }
  } catch (error) {
    check(false, `${contract.file} has an invalid MP4 atom structure: ${error.message}`);
  }
}

for (const contract of imageContracts) {
  if (!exists(contract.file)) continue;
  check(
    size(contract.file) <= contract.budgetBytes,
    `${contract.file} exceeds its ${contract.budgetBytes / 1024} KiB budget documented in docs/asset-integrity.md.`,
  );
}

// Site posters and editorial artwork are WebP rather than package-supplied
// PNG/JPEG files. Check the actual RIFF/WEBP signature so a renamed image
// cannot silently satisfy the path list.
for (const file of [...new Set([...expectedPosters, ...expectedArtwork])]) {
  if (!exists(file)) continue;
  const buffer = readFileSync(absolute(file));
  check(
    buffer.length >= 12 &&
      buffer.toString("ascii", 0, 4) === "RIFF" &&
      buffer.toString("ascii", 8, 12) === "WEBP",
    `${file} must be a real WebP image, not only use a .webp extension.`,
  );
}

// Mobile derivatives: the same edit as their desktop parents (duration inside
// a tight envelope) but never byte-for-byte identical to them.
if (ffprobe) {
  for (const contract of videoContracts) {
    if (!contract.durationOf || !exists(contract.file) || !exists(contract.durationOf)) continue;
    const derived = probeDuration(ffprobe, contract.file);
    const parent = probeDuration(ffprobe, contract.durationOf);
    check(
      derived !== null && parent !== null && Math.abs(derived - parent) <= 0.2,
      `${contract.file} duration (${derived}s) must match ${contract.durationOf} (${parent}s) within 0.2s — same edit, same exclusions.`,
    );
  }
}
for (const contract of videoContracts) {
  if (!contract.duplicateOf || !exists(contract.file) || !exists(contract.duplicateOf)) continue;
  check(
    sha256(contract.file) !== sha256(contract.duplicateOf),
    `${contract.file} must be a re-encoded derivative, not a byte-for-byte copy of ${contract.duplicateOf}.`,
  );
}

// WebVTT captions: valid, ordered, non-overlapping cues contained within the
// film's duration, and free of unsupported claims or private addresses.
const vttTimestamp = String.raw`(?:\d{2}:)?\d{2}:\d{2}\.\d{3}`;
const vttCueLine = new RegExp(`^(${vttTimestamp}) --> (${vttTimestamp})(?: .*)?$`);
function vttSeconds(stamp) {
  const parts = stamp.split(":").map(Number);
  return parts.length === 3
    ? parts[0] * 3600 + parts[1] * 60 + parts[2]
    : parts[0] * 60 + parts[1];
}
for (const { file, video } of captionContracts) {
  check(exists(file), `${file} is missing.`);
  if (!exists(file)) continue;
  const text = readFileSync(absolute(file), "utf8");
  check(text.startsWith("WEBVTT"), `${file} must start with WEBVTT.`);

  const cues = [];
  for (const line of text.split(/\r?\n/)) {
    if (!line.includes("-->")) continue;
    const match = line.trim().match(vttCueLine);
    check(Boolean(match), `${file} has an invalid cue timing line: "${line.trim()}".`);
    if (match) cues.push([vttSeconds(match[1]), vttSeconds(match[2])]);
  }
  check(cues.length >= 1, `${file} must contain at least one cue.`);
  cues.forEach(([start, end], index) => {
    check(start < end, `${file}: cue ${index + 1} must end after it starts.`);
    if (index > 0) {
      check(
        cues[index - 1][1] <= start,
        `${file}: cues must be ordered and non-overlapping (cue ${index + 1}).`,
      );
    }
  });
  if (ffprobe && exists(video) && cues.length > 0) {
    const duration = probeDuration(ffprobe, video);
    check(
      duration !== null && cues[cues.length - 1][1] <= duration,
      `${file}: the final cue must end within ${video}'s duration.`,
    );
  }
  check(
    !/daichunyu666@gmail\.com|charles@madebymotionx\.com/.test(text),
    `${file} must not contain a private address.`,
  );
  check(
    !/(trusted by|clients include|award|testimonial|conversion|clinicall|cures?\b|treats\b|heals\b|therapeutic|efficacy)/i.test(
      text,
    ),
    `${file} must not introduce client/result/medical claims — captions describe verified audible content only.`,
  );
}

for (const file of expectedOgCards) {
  if (!exists(file)) continue;
  const dimensions = jpegDimensions(file);
  check(Boolean(dimensions), `${file} must be a valid JPEG image.`);
  if (dimensions) {
    check(
      dimensions.width === 1200 && dimensions.height === 630,
      `${file} must be 1200x630; found ${dimensions.width}x${dimensions.height}.`,
    );
  }
}

if (skips.length > 0) {
  console.warn("MOTIONX asset-integrity CI skips:");
  for (const skip of skips) console.warn(`- ${skip}`);
}

if (failures.length > 0) {
  console.error("MOTIONX asset-integrity check failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

const skipSummary = skips.length > 0 ? `, ${skips.length} CI-only skips` : "";
console.log(`MOTIONX asset-integrity check passed (${checks} checks${skipSummary}).`);
