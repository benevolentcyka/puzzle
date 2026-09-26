'use strict';
// These hashes identify the precise byte hypotheses used by the GPU checkpoints.
// Checking them catches Git newline conversion before a search can resume.
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const expected = {
  'four-groups-crlfcrlf.txt': '13111461205a1a1ef5aff37f84c532998777555b43c543383b3c7a057f92f9ec',
  'four-groups-lflf.txt': 'f982ecaf53e92b6ccb3709231ae82eba6d46465562e34b6c919ca1fdb858a69b',
  'raw-crlfcrlf.txt': 'd81c4291774f25a1d5e25389f2f99317fcc8528e950cd2d0e35680ca82adfa14',
  'raw-lflf.txt': '997519617c1132a6e97e164c153856da707282062baa050188a421324887de52',
  'three-groups-crlfcrlf.txt': 'f196a21efd85f337ce16b1c2e9cb976a1ab34f1fd1b78a277c14688edb82c8d4',
  'three-groups-lflf.txt': '4adda48a39083008765db842e32a7021c3a97c9d757ea1a624aaa96055b087c5',
};
for (const [name, sha] of Object.entries(expected)) {
  const bytes = fs.readFileSync(path.join(__dirname, 'bases', name));
  const actual = crypto.createHash('sha256').update(bytes).digest('hex');
  if (actual !== sha) throw new Error(`${name}: byte hash changed (${actual}). Regenerate with make-search-bases.py and inspect the change.`);
  const letters = [...bytes].filter(b => b >= 65 && b <= 90 || b >= 97 && b <= 122).length;
  if (letters !== 35825) throw new Error(`${name}: ASCII letter count changed`);
  const stateFile = path.join(__dirname, `pair-state-${path.parse(name).name}-index0.json`);
  if (fs.existsSync(stateFile)) {
    const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    if (state.base_sha256 !== sha || state.pairs_total !== letters * (letters - 1) / 2 ||
        !Number.isSafeInteger(state.next_rank) || state.next_rank < 0 || state.next_rank > state.pairs_total) {
      throw new Error(`${name}: checkpoint does not identify this exact pair space`);
    }
  }
}
console.log('PASS: six exact-byte bases, 35,825 ASCII letters each, and saved checkpoint identities');
