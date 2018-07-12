import os
from decimal import Decimal

import pytest

from polyglotdb import CorpusContext

acoustic = pytest.mark.skipif(
    pytest.config.getoption("--skipacoustics"),
    reason="remove --skipacoustics option to run"
)


def test_query_intensity(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        expected_intensity = {Decimal('4.23'): {'Intensity': 98},
                              Decimal('4.24'): {'Intensity': 100},
                              Decimal('4.25'): {'Intensity': 99},
                              Decimal('4.26'): {'Intensity': 95.8},
                              Decimal('4.27'): {'Intensity': 95.8}}
        g.save_intensity('acoustic_corpus', expected_intensity)

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        q = q.columns(g.phone.label, g.phone.intensity.track)
        print(q.cypher())
        results = q.all()

        print(sorted(expected_intensity.items()))
        print(results[0].track)
        for point in results[0].track:
            assert (round(point['Intensity'], 1) == expected_intensity[point.time]['Intensity'])


def test_relativize_intensity(acoustic_utt_config):
    with CorpusContext(acoustic_utt_config) as g:
        mean_f0 = 97.72
        sd_f0 = 1.88997
        expected_intensity = {Decimal('4.23'): {'Intensity': 98, 'Intensity_relativized': (98 - mean_f0) / sd_f0},
                              Decimal('4.24'): {'Intensity': 100, 'Intensity_relativized': (100 - mean_f0) / sd_f0},
                              Decimal('4.25'): {'Intensity': 99, 'Intensity_relativized': (99 - mean_f0) / sd_f0},
                              Decimal('4.26'): {'Intensity': 95.8, 'Intensity_relativized': (95.8 - mean_f0) / sd_f0},
                              Decimal('4.27'): {'Intensity': 95.8, 'Intensity_relativized': (95.8 - mean_f0) / sd_f0}}
        g.relativize_intensity(by_speaker=True)
        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        ac = g.phone.intensity
        ac.relative = True
        q = q.columns(g.phone.label, ac.track)
        results = q.all()
        assert (len(results[0].track) == len(expected_intensity.items()))
        print(sorted(expected_intensity.items()))
        print(results[0].track)
        for point in results[0].track:
            print(point)
            assert (round(point['Intensity'], 5) == round(expected_intensity[point.time]['Intensity_relativized'], 5))

        g.reset_relativized_intensity()

        q = g.query_graph(g.phone)
        q = q.filter(g.phone.label == 'ow')
        q = q.order_by(g.phone.begin.column_name('begin'))
        ac = g.phone.intensity
        ac.relative = True
        q = q.columns(g.phone.label, ac.track)
        results = q.all()
        assert len(results[0].track) == 0


@acoustic
def test_analyze_intensity_basic_praat(acoustic_utt_config, praat_path, results_test_dir):
    with CorpusContext(acoustic_utt_config) as g:
        g.config.praat_path = praat_path
        g.analyze_intensity()
        assert (g.has_intensity(g.discourses[0]))
        q = g.query_graph(g.phone).filter(g.phone.label == 'ow')
        q = q.columns(g.phone.begin, g.phone.end, g.phone.intensity.track)
        results = q.all()
        output_path = os.path.join(results_test_dir, 'intensity_data.csv')
        q.to_csv(output_path)
        assert (len(results) > 0)
        for r in results:
            assert (len(r.track))

        g.reset_intensity()
        assert not g.has_intensity(g.discourses[0])
