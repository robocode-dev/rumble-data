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
            "battleId": battle_id, "completedAt": "2026-08-02T12:00:00Z", "client": {"id": "alice-desktop", "version": "0.1.0"}, "engine": {"behaviorVersion": behavior_version},
            "gameType": "1v1", "rounds": 35, "arenaWidth": 800, "arenaHeight": 600,
            "participants": [self.participant("Alpha", rank=1, total_score=80, first_places=35), self.participant("Bravo", rank=2, total_score=20, second_places=35)],
        }]}

    @staticmethod
    def participant(name: str, *, rank: int, total_score: int, first_places: int = 0, second_places: int = 0, third_places: int = 0) -> dict:
        return {"name": name, "version": "1.0", "isTeam": False, "rank": rank, "totalScore": total_score, "survival": 0, "lastSurvivorBonus": 0, "bulletDamage": 0, "bulletKillBonus": 0, "ramDamage": 0, "ramKillBonus": 0, "firstPlaces": first_places, "secondPlaces": second_places, "thirdPlaces": third_places}

    def testRDA001_IntegrationPositive_valid_batch_becomes_immutable_fact_and_projections(self) -> None:
        outcomes = ingest(self.root, self.envelope(), account="alice")
        self.assertTrue(outcomes[0].accepted)
        self.assertTrue((self.root / "results/raw/2026/08" / f"{outcomes[0].accepted.digest}.json").is_file())
        aggregate(self.root)
        leaderboard = json.loads((self.root / "leaderboard/1v1.json").read_text(encoding="utf-8"))
        self.assertEqual("Alpha", leaderboard["entries"][0]["name"])
        needed = json.loads((self.root / "matchmaking/matches_needed-1v1.json").read_text(encoding="utf-8"))
        self.assertIn(["Alpha 1.0", "Charlie 1.0"], [pair["bots"] for pair in needed["priorityPairs"]])

    def testRDA001_IntegrationPositive_valid_records_survive_invalid_batch_neighbors(self) -> None:
        envelope = self.envelope()
        invalid = self.envelope(battle_id="a290f1ee-6c54-4b01-90e6-d701748f0851")["results"][0]
        invalid["participants"][0].pop("rank")
        envelope["results"].append(invalid)
        outcomes = ingest(self.root, envelope, account="alice")
        self.assertTrue(outcomes[0].accepted)
        self.assertIsNone(outcomes[1].accepted)
        self.assertIn("rank", outcomes[1].error)
        self.assertEqual(1, len(list((self.root / "results/raw").rglob("*.json"))))

    def testRDA002_IntegrationNegative_structural_and_duplicate_records_never_persist(self) -> None:
        malformed = self.envelope()["results"][0]
        malformed.pop("rounds")
        outcome = ingest(self.root, {**self.envelope(), "results": [malformed]}, account="alice")[0]
        self.assertIsNone(outcome.accepted)
        self.assertIn("rounds", outcome.error)
        self.assertFalse((self.root / "results/raw").exists())
        self.assertTrue(ingest(self.root, self.envelope(), account="alice")[0].accepted)
        duplicate = ingest(self.root, self.envelope(), account="alice")[0]
        self.assertIsNone(duplicate.accepted)
        self.assertIn("duplicate battleId", duplicate.error)

    def testRDA002_IntegrationNegative_rejects_each_documented_structural_violation(self) -> None:
        invalid_records = []
        cases = (
            ("a290f1ee-6c54-4b01-90e6-d701748f0851", lambda record: record.update({"client": {"id": "alice-desktop", "version": "other"}}), "record client identity"),
            ("b290f1ee-6c54-4b01-90e6-d701748f0851", lambda record: record["engine"].update({"behaviorVersion": True}), "engine.behaviorVersion"),
            ("c290f1ee-6c54-4b01-90e6-d701748f0851", lambda record: record.update({"arenaWidth": 801}), "arena dimensions"),
            ("d290f1ee-6c54-4b01-90e6-d701748f0852", lambda record: record["participants"][0].update({"isTeam": True}), "isTeam"),
            ("e290f1ee-6c54-4b01-90e6-d701748f0851", lambda record: record["participants"][0].update({"totalScore": 1.5}), "totalScore"),
            ("f290f1ee-6c54-4b01-90e6-d701748f0851", lambda record: record["participants"][1].update({"rank": 3}), "1224"),
            ("0290f1ee-6c54-4b01-90e6-d701748f0851", lambda record: record["participants"][0].update({"firstPlaces": 36}), "firstPlaces"),
            ("1290f1ee-6c54-4b01-90e6-d701748f0851", lambda record: (record["participants"][0].update({"secondPlaces": 1}), record["participants"][1].update({"secondPlaces": 34})), "participant place counts"),
        )
        for battle_id, mutate, expected_error in cases:
            record = self.envelope(battle_id=battle_id)["results"][0]
            mutate(record)
            invalid_records.append((record, expected_error))
        envelope = self.envelope()
        envelope["results"] = [record for record, _ in invalid_records]
        outcomes = ingest(self.root, envelope, account="alice")
        for outcome, (_, expected_error) in zip(outcomes, invalid_records):
            self.assertIsNone(outcome.accepted)
            self.assertIn(expected_error, outcome.error)
        self.assertFalse((self.root / "results/raw").exists())

    def testRDA001_IntegrationPositive_twinduel_requires_team_result_entries(self) -> None:
        self.write("engine.json", {"schemaVersion": 1, "behaviorVersion": 1, "gameTypes": {"twinduel": {"rounds": 75, "battlefield": [800, 800], "participants": 4}}})
        self.write("catalog.json", {"schemaVersion": 1, "bots": [
            {"name": "Alpha Team", "version": "1.0", "platform": "Python", "owner": "alpha-owner", "status": "active"},
            {"name": "Bravo Team", "version": "1.0", "platform": "Python", "owner": "bravo-owner", "status": "active"},
        ]})
        record = self.envelope()["results"][0]
        record.update({"gameType": "twinduel", "rounds": 75, "arenaWidth": 800, "arenaHeight": 800, "participants": [
            {**self.participant("Alpha Team", rank=1, total_score=80, first_places=150), "isTeam": True},
            {**self.participant("Bravo Team", rank=2, total_score=20, second_places=150), "isTeam": True},
        ]})
        self.assertTrue(ingest(self.root, {**self.envelope(), "results": [record]}, account="alice")[0].accepted)

    def testRDA003_IntegrationPositive_compaction_preserves_deterministic_projection(self) -> None:
        ingest(self.root, self.envelope(), account="alice")
        aggregate(self.root)
        before = (self.root / "leaderboard/1v1.json").read_text(encoding="utf-8")
        compact(self.root, before="2026-09-01")
        shutil.rmtree(self.root / "results/raw")
        aggregate(self.root)
        after = (self.root / "leaderboard/1v1.json").read_text(encoding="utf-8")
        self.assertEqual(before, after)

    def testRDA003_IntegrationPositive_current_bans_and_registration_filter_existing_facts(self) -> None:
        ingest(self.root, self.envelope(), account="alice")
        aggregate(self.root)
        self.assertEqual(1, json.loads((self.root / "clients.json").read_text(encoding="utf-8"))["clients"][0]["battles"])
        self.write("bans.json", {"schemaVersion": 1, "bannedAccounts": ["alice"], "disqualifiedBots": []})
        aggregate(self.root)
        self.assertEqual([], json.loads((self.root / "clients.json").read_text(encoding="utf-8"))["clients"])
        self.write("bans.json", {"schemaVersion": 1, "bannedAccounts": [], "disqualifiedBots": []})
        self.write("clients/alice.json", {"schemaVersion": 1, "account": "alice", "clientIds": []})
        aggregate(self.root)
        self.assertEqual([], json.loads((self.root / "clients.json").read_text(encoding="utf-8"))["clients"])

    def testRDA004_E2EPositive_dashboard_references_versioned_projection_and_bot_details(self) -> None:
        page = (ROOT / "site/index.html").read_text(encoding="utf-8")
        script = (ROOT / "site/app.js").read_text(encoding="utf-8")
        self.assertIn("game-type", page)
        self.assertIn("data/leaderboard/${gameType}.json", script)
        self.assertIn("data/bots/", script)


if __name__ == "__main__":
    unittest.main()
