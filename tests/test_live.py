# Python 3.11+ | tests/test_live.py | portable | local player identity, practice mode, diagnostics
import copy
import json
from pathlib import Path
import sys
import unittest
import threading
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from live import Feed, resolve_player, own_player, live_report
from engine import live_valid
import app


class LiveDataTests(unittest.TestCase):
    def setUp(self):
        self.data = copy.deepcopy(Feed(demo=True).read()[0])

    def test_practice_tool_with_alive_ezreal_is_accepted(self):
        self.data['gameData']['gameMode'] = 'PRACTICETOOL'
        report = live_report(self.data, .2)
        self.assertTrue(report['ok'])
        self.assertIn('Ferramenta de Treino', report['reason'])
        self.assertTrue(live_valid(self.data, .2))

    def test_normal_game_still_accepted(self):
        self.assertTrue(live_valid(self.data, .2))

    def test_aram_remains_outside_supported_map(self):
        self.data['gameData'].update(gameMode='ARAM', mapNumber=12)
        self.assertEqual(live_report(self.data, .2)['code'], 'wrong_map')

    def test_other_sr_mode_reports_real_mode(self):
        self.data['gameData']['gameMode'] = 'URF'
        report = live_report(self.data, .2)
        self.assertFalse(report['ok'])
        self.assertIn('URF', report['reason'])

    def test_string_map_number_and_map_name_are_read(self):
        self.data['gameData']['mapNumber'] = '11'
        self.assertTrue(live_valid(self.data, .2))
        self.data['gameData'].pop('mapNumber')
        self.data['gameData']['mapName'] = 'Map11'
        self.assertTrue(live_valid(self.data, .2))

    def test_case_whitespace_and_split_riot_id_match(self):
        self.data['activePlayer'].pop('riotId')
        self.data['activePlayer'].update(riotIdGameName=' demo ', riotIdTagLine='test')
        self.assertIs(own_player(self.data), self.data['allPlayers'][0])

    def test_unique_game_name_matches_tagged_roster(self):
        self.data['activePlayer'].pop('riotId')
        self.data['activePlayer']['riotIdGameName'] = 'DEMO'
        own, method = resolve_player(self.data)
        self.assertIs(own, self.data['allPlayers'][0])
        self.assertEqual(method, 'unique_game_name')

    def test_shared_game_name_does_not_pick_arbitrary_player(self):
        self.data['activePlayer'].pop('riotId')
        self.data['activePlayer']['riotIdGameName'] = 'DEMO'
        self.data['allPlayers'].append(dict(self.data['allPlayers'][0], riotId='DEMO#OTHER'))
        self.assertEqual(resolve_player(self.data), (None, 'ambiguous'))

    def test_different_explicit_tags_are_not_merged(self):
        self.data['activePlayer']['riotId'] = 'DEMO#WRONG'
        self.assertIsNone(own_player(self.data))

    def test_full_id_wins_over_shared_legacy_name(self):
        self.data['activePlayer']['summonerName'] = 'Legacy'
        self.data['allPlayers'][0]['summonerName'] = 'Legacy'
        self.data['allPlayers'].append(dict(riotId='Opponent#OTHER', summonerName='Legacy', championName='Ahri'))
        self.assertIs(own_player(self.data), self.data['allPlayers'][0])

    def test_no_ids_can_use_two_active_ezreal_ability_ids(self):
        self.data['activePlayer'].pop('riotId')
        own, method = resolve_player(self.data)
        self.assertIs(own, self.data['allPlayers'][0])
        self.assertEqual(method, 'active_abilities')

    def test_ability_fallback_does_not_guess_in_mirror_match(self):
        self.data['activePlayer'].pop('riotId')
        self.data['allPlayers'].append(dict(self.data['allPlayers'][0], riotId='Other#EZ'))
        self.assertIsNone(own_player(self.data))

    def test_just_an_enemy_ezreal_is_not_enough(self):
        self.data['activePlayer'].pop('riotId')
        self.data['activePlayer']['abilities']['W']['id'] = 'AnnieW'
        self.assertIsNone(own_player(self.data))

    def test_raw_champion_key_can_identify_localized_champion(self):
        self.data['allPlayers'][0].update(championName='Localized label', rawChampionName='game_character_displayname_Ezreal')
        self.assertTrue(live_valid(self.data, .2))

    def test_loading_attributes_are_distinguished_from_wrong_champion(self):
        self.data['activePlayer']['championStats'] = {}
        report = live_report(self.data, .2)
        self.assertEqual(report['code'], 'loading_stats')
        self.assertEqual(report['champion'], 'Ezreal')

    def test_zero_health_or_attack_speed_does_not_enable_input(self):
        for key in ('currentHealth', 'attackSpeed'):
            data = copy.deepcopy(self.data)
            data['activePlayer']['championStats'][key] = 0
            self.assertFalse(live_valid(data, .2))

    def test_no_api_and_stale_data_get_different_diagnostics(self):
        self.assertEqual(live_report({}, 50, 'Porta não respondeu')['code'], 'no_data')
        self.assertEqual(live_report(self.data, 5)['code'], 'stale')

    def test_calibration_can_read_slightly_older_snapshot_without_enabling_input(self):
        self.assertTrue(live_report(self.data, 2, max_age=3)['ok'])
        self.assertFalse(live_valid(self.data, 2))

    def test_diagnostic_omits_account_identifiers(self):
        text = json.dumps(live_report(self.data, .2))
        self.assertNotIn('DEMO#TEST', text)
        self.assertNotIn('ALVO#DEMO', text)
        self.assertNotIn('summonerName', text)

    def test_dead_player_has_explicit_reason(self):
        self.data['allPlayers'][0]['isDead'] = True
        self.assertEqual(live_report(self.data, .2)['code'], 'dead')

    def capture_app(self):
        obj = app.Application.__new__(app.Application)
        obj.demo, obj.inputs = False, object()
        obj.armed = threading.Event()
        obj.armed.set()
        data = self.data
        class FeedStub:
            def read(self): return data, .2, 'Conectado'
        class RootStub:
            withdrawn = False
            scheduled = None
            def withdraw(self): self.withdrawn = True
            def after(self, delay, callback): self.scheduled = (delay, callback)
        obj.feed, obj.root = FeedStub(), RootStub()
        return obj

    def test_practice_capture_is_scheduled_instead_of_generic_error(self):
        self.data['gameData']['gameMode'] = 'PRACTICETOOL'
        obj = self.capture_app()
        with patch('app.messagebox.showerror') as error:
            obj.capture('automatic')
        error.assert_not_called()
        self.assertTrue(obj.root.withdrawn)
        self.assertEqual(obj.root.scheduled[0], 3000)
        self.assertFalse(obj.armed.is_set())

    def test_bad_state_is_explained_before_hiding_app(self):
        self.data['gameData']['gameMode'] = 'URF'
        obj = self.capture_app()
        with patch('app.messagebox.showerror') as error:
            obj.capture('automatic')
        self.assertFalse(obj.root.withdrawn)
        self.assertIsNone(obj.root.scheduled)
        self.assertIn('URF', error.call_args.args[1])
        self.assertFalse(obj.armed.is_set())


if __name__ == '__main__':
    unittest.main()
