'use strict';
// Read-only live prize check. Writes an explicitly dated evidence snapshot.
const fs = require('fs');
const path = require('path');
const TARGET = '14zMkTgaVXJcxdh4JdWi29MLRR44iUSG9W';
const FUNDING = 'a1916e7ed9eac3fcc56a55056328cb09d06925e2694f2e6720de12b228514d1f';
async function main() {
  const failures = [];
  for (const provider of ['https://mempool.space/api', 'https://blockstream.info/api']) {
    try {
      const url = `${provider}/address/${TARGET}/utxo`;
      const response = await fetch(url, {signal: AbortSignal.timeout(30000)});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const utxos = await response.json();
      if (!Array.isArray(utxos)) throw new Error('Unexpected UTXO schema');
      const funded = utxos.find(o => o.txid === FUNDING && o.vout === 1 && o.value === 77700000);
      const report = {
        checked_utc: new Date().toISOString(), source_url: url, address: TARGET,
        expected_funding_txid: FUNDING, expected_output: 1, expected_sats: 77700000,
        expected_output_unspent: Boolean(funded), utxos, earlier_provider_failures: failures,
      };
      fs.writeFileSync(path.join(__dirname, 'chain-status.json'), JSON.stringify(report, null, 2) + '\n');
      console.log(JSON.stringify({checked_utc: report.checked_utc, expected_output_unspent: report.expected_output_unspent}));
      return;
    } catch (e) { failures.push({provider, error: String(e)}); }
  }
  throw new Error(`No live chain check succeeded: ${JSON.stringify(failures)}`);
}
main().catch(e => {console.error(e); process.exitCode = 1;});
