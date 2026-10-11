"""Checks of the corrected hydrogen manuscript, not a full symbolic proof."""
from math import exp, sqrt
from pathlib import Path
import tempfile
import unittest

from site_content.latex import convert_document

ROOT = Path(__file__).resolve().parents[2]


class HydrogenTests(unittest.TestCase):
    def test_corrected_manuscript_is_explicit_and_original_is_retained(self):
        source = (ROOT / 'Quantum_Mechanics.tex').read_text(encoding='utf-8')
        original = (ROOT / 'notebook_sources/originals/Quantum_Mechanics.original.tex').read_text(encoding='utf-8')
        self.assertIn('Editorially corrected reader edition', source)
        self.assertIn(r'e^{-\rho/2}\rho^\ell L_{n-\ell-1}^{2\ell+1}(\rho)', source)
        self.assertIn(r'\mu=m_e m_p/(m_e+m_p)', source)
        self.assertIn('Condon--Shortley', source)
        self.assertIn(r'e^{-\rho}F', original)
        self.assertNotEqual(source, original)

    def test_lowest_radial_states_normalize_with_the_volume_measure(self):
        # Dimensionless radius x=r/a_mu; radial functions are scaled by a_mu^1.5.
        functions = [lambda x: 2*exp(-x),
                     lambda x: (2-x)*exp(-x/2)/(2*sqrt(2)),
                     lambda x: x*exp(-x/2)/(2*sqrt(6))]
        dx, steps = 0.002, 30000
        for function in functions:
            integral = sum(function((i+.5)*dx)**2*((i+.5)*dx)**2*dx for i in range(steps))
            self.assertAlmostEqual(integral, 1, places=9)

    def test_ground_state_radial_differential_equation(self):
        for x in (.1, .5, 1., 2., 10.):
            r = exp(-x)
            # Analytic derivatives R'=-R and R''=R.
            self.assertAlmostEqual(r - 2*r/x + (-1+2/x)*r, 0, places=12)

    def test_reader_has_no_conversion_warnings_or_unresolved_references(self):
        with tempfile.TemporaryDirectory() as directory:
            result = convert_document(ROOT / 'Quantum_Mechanics.tex', ROOT,
                                      Path(directory), 'assets')
        self.assertEqual(result['warnings'], [])
        self.assertEqual(len(result['headings']), 6)
        self.assertEqual(result['equation_count'], 9)


class FragmentImageTests(unittest.TestCase):
    def test_explicit_root_resolves_images_but_does_not_relax_confinement(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            images = root / 'images'
            images.mkdir()
            (images / 'plot.png').write_bytes(b'fixture')
            (root / 'private.png').write_bytes(b'private')
            source = root / 'nested' / 'notes.tex'
            source.parent.mkdir()
            source.write_text(r'\includegraphics{images/plot.png}', encoding='utf-8')
            result = convert_document(source, images, root / 'assets', 'assets', source_root=root)
            self.assertEqual(result['image_count'], 1)
            self.assertEqual((root / 'assets/plot.png').read_bytes(), b'fixture')
            source.write_text(r'\includegraphics{private.png}', encoding='utf-8')
            with self.assertRaises(FileNotFoundError):
                convert_document(source, images, root / 'other-assets', 'assets', source_root=root)
            self.assertFalse((root / 'other-assets').exists())


if __name__ == '__main__':
    unittest.main()