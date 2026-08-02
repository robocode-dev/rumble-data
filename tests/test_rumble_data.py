"""Focused integration and dashboard evidence for the Rumble data repository."""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from aggregate import aggregate
from compact import compact
from ingest import ingest
from validate import ValidationError


class RumbleDataTests(unittest.TestCase):
    """Exercise repository contracts through the public script functions."""

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "clients").mkdir()
        self.write("engine.json", {"schemaVersion": 1, "behaviorVersion": 1, "gameTypes": {"1v1": {"rounds": 35, "battlefield": [800, 600], "participants": 2}}})
        self.write("bans.json", {"schemaVersion": 1, "bannedAccounts": [], "disqualifiedBots": []})
        self.write("exclusions.json", {"schemaVersion": 1, "battleIds": []})
        self.write("clients/alice.json", {"schemaVersion": 1, "account": "alice", "clientIds": ["alice-desktop"]})
        self.write("catalog.json", {"schemaVersion": 1, "bots": [
            {"name": "Alpha", "version": "1.0", "platform": "Python", "owner": "alpha-owner", "status": "active"},
            {"name": "Bravo", "version": "1.0", "platform": "Python", "owner": "bravo-owner", "status": "active"},
            {"name": "Charlie", "version": "1.0", "platform": "Python", "owner": "charlie-owner", "status": "active"},
        ]})

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write(self, relative: str, value: object) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def envelope(self, *, battle_id: str = "d290f1ee-6c54-4b01-90e6-d701748f0851", behavior_version: int = 1) -> dict:
        return {"schemaVersion": 1, "clientId": "alice-desktop", "clientVersion": "0.1.0", "results": [{
            "battleId": battle_id, "completedAt": "2026-08-02T12:00:00Z", "clientId": "alice-desktop", "behaviorVersion": behavior_version, "gameType": "1v1", "numberOfRounds": 35, "battlefield": [800, 600],
            "participants": [self.participant("Alpha", 1, 80, 35), self.participant("Bravo", 2, 20, 0)],
        }]}

    def participant(self, name: str, rank: int, score: int, first_places: int) -> dict:
        return {"name": name, "version": "1.0", "isTeam": False, "rank": rank, "totalScore": score, "survival": score, "lastSurvivorBonus": 0, "bulletDamage": 0, "bulletKillBonus": 0, "ramDamage": 0, "ramKillBonus": 0, "firstPlaces": first_places, "secondPlaces": 0, "thirdPlaces": 0}

    def testRDA001_IntegrationPositive_valid_batch_becomes_immutable_fact_and_projections(self) -> None:
        paths, rejected = ingest(self.root, self.envelope(), account="alice")
        self.assertEqual(1, len(paths))
        self.assertEqual([], rejected)
        self.assertTrue((self.root / paths[0]).is_file())
        aggregate(self.root)
        leaderboard = json.loads((self.root / "leaderboard/1v1.json").read_text(encoding="utf-8"))
        self.assertEqual("Alpha", leaderboard["entries"][0]["name"])
        needed = json.loads((self.root / "matchmaking/matches_needed-1v1.json").read_text(encoding="utf-8"))
        self.assertIn(["Alpha 1.0", "Charlie 1.0"], [pair["bots"] for pair in needed["priorityPairs"]])

    def testRDA002_IntegrationNegative_incompatible_or_duplicate_records_leave_no_new_fact(self) -> None:
        paths, rejected = ingest(self.root, self.envelope(behavior_version=2), account="alice")
        self.assertEqual([], paths)
        self.assertTrue(any("behaviorVersion" in item for item in rejected))
        self.assertFalse((self.root / "results/raw").exists())
        ingest(self.root, self.envelope(), account="alice")
        _, rejected = ingest(self.root, self.envelope(), account="alice")
        self.assertTrue(any("duplicate battleId" in item for item in rejected))

    def testRDA001_IntegrationPositive_mixed_batch_retains_valid_record_and_reports_invalid_record(self) -> None:
        envelope = self.envelope()
        invalid = self.envelope(battle_id="00000000-0000-0000-0000-000000000001")["results"][0]
        invalid["participants"][0]["totalScore"] = 999
        envelope["results"].append(invalid)
        paths, rejected = ingest(self.root, envelope, account="alice")
        self.assertEqual(1, len(paths))
        self.assertEqual(1, len(rejected))
        self.assertIn("totalScore", rejected[0])

    def testRDA003_IntegrationPositive_compaction_preserves_deterministic_projection(self) -> None:
        ingest(self.root, self.envelope(), account="alice")
        aggregate(self.root)
        before = (self.root / "leaderboard/1v1.json").read_text(encoding="utf-8")
        archive = self.root / "archive"
        compact(self.root, before="2026-09-01", archive_root=archive)
        self.assertTrue((archive / "results/raw/2026/08").exists())
        after = (self.root / "leaderboard/1v1.json").read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def testRDA004_E2EPositive_dashboard_references_versioned_projection_and_bot_details(self) -> None:
        page = (ROOT / "site/index.html").read_text(encoding="utf-8")
        script = (ROOT / "site/app.js").read_text(encoding="utf-8")
        self.assertIn("game-type", page)
        self.assertIn("data/leaderboard/${gameType}.json", script)
        self.assertIn("data/bots/", script)
        self.assertIn("data-sort", page)
        self.assertIn("renderEntries", script)


if __name__ == "__main__":
    unittest.main()
