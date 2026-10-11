"""Safe PDF cache contracts; fixtures contain no real private metadata.

The real public report staging test retains the original privacy validators.
Mocked compiler tests exercise process boundaries; actual Tectonic runs are an
explicit CLI task, never an implicit test/build dependency.
"""

from contextlib import redirect_stdout
from hashlib import sha256
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from PIL import Image

from site_content import pdf


ROOT = Path(__file__).resolve().parents[2]


def engine_process(run):
    # Replace only pdf's module reference, not the shared subprocess.run used
    # by the real Pandoc converter (which also uses subprocess.run).
    return patch.object(pdf, "subprocess", SimpleNamespace(run=run))


def unexpected_engine(*args, **kwargs):
    raise AssertionError("Unexpected TeX invocation")


def small_pdf() -> bytes:
    """A complete one-page PDF with genuine xref offsets, not a header stub."""
    data = b"%PDF-1.5\n"
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>",
               b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>"]
    offsets = [0]
    for number, body in enumerate(objects, 1):
        offsets.append(len(data))
        data += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref = len(data)
    data += b"xref\n0 4\n0000000000 65535 f \n"
    data += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:])
    return data + f"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()


class PdfFixtureTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="pdf-fixture-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.key = "basketball-rules"
        self.source = self.root / pdf.DOCUMENTS[self.key]
        self.source.parent.mkdir(parents=True)
        self.source.write_text(
            r"\documentclass[11pt]{article}" + "\n" + r"\usepackage{graphicx}" + "\n" +
            r"\begin{document}" + "\nA public fixture.\n" +
            r"\includegraphics[width=1in]{tex_images/sports/example.png}" + "\n" +
            r"\end{document}" + "\n", encoding="utf-8")
        self.image = self.root / "tex_images/sports/example.png"
        self.image.parent.mkdir(parents=True)
        Image.new("RGB", (4, 3), "white").save(self.image)
        self.cached = self.root / pdf.CACHE / f"{self.key}.pdf"
        self.manifest_path = self.cached.with_suffix(".json")
        self.assets = self.root / "output-assets"
        self.process_calls = []

    def fake_engine(self, args, **kwargs):
        self.process_calls.append((args, kwargs))
        stage = Path(kwargs["cwd"])
        self.assertFalse(kwargs.get("shell", False))
        self.assertEqual(kwargs["env"]["SOURCE_DATE_EPOCH"], pdf.EPOCH)
        self.assertEqual(kwargs["env"]["TECTONIC_UNTRUSTED_MODE"], "1")
        if args[-1] == "--version":
            return subprocess.CompletedProcess(args, 0, "Tectonic 0.17.0\n", "")
        self.assertEqual(args[1:], [*pdf.FLAGS, "document.tex"])
        self.assertFalse(stage.is_relative_to(self.root))
        self.assertEqual({p.relative_to(stage).as_posix() for p in stage.rglob("*") if p.is_file()},
                         {"document.tex", "tex_images/sports/example.png"})
        self.assertEqual((stage / "document.tex").read_bytes(), self.source.read_bytes())
        self.assertEqual((stage / "tex_images/sports/example.png").read_bytes(), self.image.read_bytes())
        (stage / "output/document.pdf").write_bytes(small_pdf())
        (stage / "output/document.log").write_text("No warnings.\n", encoding="utf-8")
        return subprocess.CompletedProcess(args, 0, "", "")

    def compile(self):
        # The mocked engine is only the subprocess boundary; converters and path
        # validation use real temporary inputs and real Pandoc conversion.
        with engine_process(self.fake_engine), redirect_stdout(io.StringIO()):
            return pdf.compile_document(self.root, self.key, Path(sys.executable))

    def mutate_manifest(self, mutation):
        manifest = json.loads(self.manifest_path.read_bytes())
        mutation(manifest)
        self.manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    def refused_copy(self):
        with self.assertRaisesRegex(ValueError, "recompile.*site_content.pdf"):
            pdf.copy_verified_pdf(self.root, self.key, self.assets)
        self.assertFalse((self.assets / "document.pdf").exists())

    def test_missing_cache_returns_none_without_source_read_engine_or_asset_write(self):
        self.source.unlink()
        with patch.object(pdf, "_stage", side_effect=AssertionError("Unexpected source read")), \
            engine_process(unexpected_engine):
            self.assertIsNone(pdf.copy_verified_pdf(self.root, self.key, self.assets))
        self.assertFalse(self.assets.exists())

    def test_current_cache_copies_exact_filename_without_compiling(self):
        result = self.compile()
        self.assertEqual(result["bytes"], len(small_pdf()))
        with engine_process(unexpected_engine):
            self.assertEqual(pdf.copy_verified_pdf(self.root, self.key, self.assets), "document.pdf")
        self.assertEqual((self.assets / "document.pdf").read_bytes(), small_pdf())
        self.assertEqual(len(self.process_calls), 2)
        self.assertTrue(all(not Path(kwargs["cwd"]).exists() for _, kwargs in self.process_calls))

    def test_manifest_is_deterministic_precise_and_contains_no_machine_paths(self):
        self.compile()
        before = self.manifest_path.read_bytes()
        manifest = json.loads(before)
        self.assertEqual(manifest["inputs"], {
            "source": {"path": pdf.DOCUMENTS[self.key], "sha256": sha256(self.source.read_bytes()).hexdigest()},
            "images": [{"path": "tex_images/sports/example.png", "archive": "tex_images/sports/example.png",
                        "sha256": sha256(self.image.read_bytes()).hexdigest()}],
        })
        self.assertNotIn(str(self.root).encode(), before)
        self.assertNotIn(str(Path(sys.executable)).encode(), before)
        self.assertNotIn(b"timestamp", before)
        self.compile()
        self.assertEqual(before, self.manifest_path.read_bytes())
        self.assertEqual(set(p.name for p in self.cached.parent.iterdir()),
                         {f"{self.key}.pdf", f"{self.key}.json"})

    def test_each_incomplete_cache_is_rejected(self):
        self.compile()
        original = self.cached.read_bytes()
        self.cached.unlink()
        self.refused_copy()
        self.cached.write_bytes(original)
        self.manifest_path.unlink()
        self.refused_copy()

    def test_stale_source_even_comment_only_is_rejected(self):
        self.compile()
        self.source.write_bytes(self.source.read_bytes() + b"% changed\n")
        self.refused_copy()

    def test_changed_or_missing_image_is_rejected(self):
        self.compile()
        Image.new("RGB", (4, 3), "blue").save(self.image)
        self.refused_copy()
        self.image.unlink()
        self.refused_copy()

    def test_corrupt_non_pdf_and_truncated_outputs_are_rejected_even_with_updated_hash(self):
        self.compile()
        for data in (b"not a PDF", small_pdf()[:-8], small_pdf().replace(b"startxref\n", b"startxref\n999999")):
            with self.subTest(case=len(data)):
                self.cached.write_bytes(data)
                self.mutate_manifest(lambda m: m.update(pdfSha256=sha256(data).hexdigest()))
                self.refused_copy()

    def test_checksum_mismatch_is_rejected(self):
        self.compile()
        self.cached.write_bytes(small_pdf().replace(b"612", b"613"))
        self.refused_copy()

    def test_mismatched_tainted_and_malformed_manifests_are_rejected(self):
        self.compile()
        good = self.manifest_path.read_bytes()
        changes = [lambda m: m.update(key="creator-pitch"), lambda m: m.update(schemaVersion=99),
                   lambda m: m.update(schemaVersion=True),
                   lambda m: m.update(extra="unexpected fixture metadata"),
                   lambda m: m["inputs"]["source"].update(path="../../outside.tex"),
                   lambda m: m["inputs"]["images"][0].update(archive="../../outside.png"),
                   lambda m: m["inputs"].update(images=[]),
                   lambda m: m["compiler"].update(version="Tectonic 0.17.0 private-fixture"),
                   lambda m: m["compiler"].update(flags=[])]
        for change in changes:
            self.manifest_path.write_bytes(good)
            self.mutate_manifest(change)
            self.refused_copy()
        for data in (b"{", b"[]", b'{"key":1,"key":2}'):
            self.manifest_path.write_bytes(data)
            self.refused_copy()

    def test_unknown_key_never_becomes_a_filesystem_path(self):
        for key in ("../../secret", "C:/fixture", "unknown"):
            with self.assertRaisesRegex(ValueError, "Unknown PDF"):
                pdf.copy_verified_pdf(self.root, key, self.assets)

    def test_tex_file_reads_dynamic_commands_and_image_paths_are_rejected(self):
        good = self.source.read_bytes()
        for payload in (r"\input{../../outside}", r"\openin1=outside", r"\write18{anything}",
                        r"\csname input\endcsname", r"^^5cinput{outside}",
                        r"\let\workreportsection\usepackage", r"\usepackage{../../outside}",
                        r"\usepackage\textbf", r"\special{pdf: anything}"):
            self.source.write_bytes(good.replace(b"A public fixture.", payload.encode()))
            with self.assertRaises(ValueError):
                pdf._stage(self.root, self.key, self.root / "stage")
        for name in ("../../outside.png", "tex_images/sports/../outside.png", "C:/outside.png",
                     "tex_images/sports/example.svg", "tex_images/sports/example.png:stream"):
            self.source.write_bytes(good.replace(b"tex_images/sports/example.png", name.encode()))
            with self.assertRaises(ValueError):
                pdf._stage(self.root, self.key, self.root / "stage")

    def test_converter_manifest_taint_is_not_used_to_read_or_write_arbitrary_files(self):
        from site_content import latex
        convert = latex.convert_document
        def taint(*args, **kwargs):
            result = convert(*args, **kwargs)
            (args[2] / "source-images.json").write_text(
                '[{"archive":"../../outside.png","asset":"../../outside.png"}]', encoding="utf-8")
            return result
        with patch.object(latex, "convert_document", side_effect=taint), self.assertRaises(ValueError):
            pdf._stage(self.root, self.key, self.root / "stage")
        self.assertFalse((self.root / "stage").exists())

    def test_failed_compilation_preserves_prior_cache_and_never_leaks_output(self):
        self.compile()
        before = self.cached.read_bytes(), self.manifest_path.read_bytes()
        def failure(args, **kwargs):
            if args[-1] == "--version":
                return self.fake_engine(args, **kwargs)
            (Path(kwargs["cwd"]) / "output/document.log").write_text(
                "! Undefined control sequence.\nl.7 synthetic-sensitive-fixture\n", encoding="utf-8")
            return subprocess.CompletedProcess(args, 1, "synthetic-sensitive-fixture", "synthetic-sensitive-fixture")
        output = io.StringIO()
        with engine_process(failure), redirect_stdout(output):
            with self.assertRaisesRegex(ValueError, "recompile") as error:
                pdf.compile_document(self.root, self.key, Path(sys.executable))
        self.assertNotIn("synthetic-sensitive-fixture", output.getvalue() + str(error.exception))
        self.assertEqual(before, (self.cached.read_bytes(), self.manifest_path.read_bytes()))

    def test_source_change_during_compile_cannot_certify_stale_input(self):
        def change(args, **kwargs):
            result = self.fake_engine(args, **kwargs)
            if args[-1] == "document.tex":
                self.source.write_bytes(self.source.read_bytes() + b"% concurrent change\n")
            return result
        with engine_process(change), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(ValueError, "recompile"):
                pdf.compile_document(self.root, self.key, Path(sys.executable))
        self.assertFalse(self.cached.exists())

    def test_success_exit_with_non_pdf_or_unresolved_diagnostics_is_refused(self):
        for log, data in (("", b"not a PDF"), ("Undefined control sequence", small_pdf()),
                          ("Missing character: fixture", small_pdf()),
                          ("LaTeX Warning: There were undefined references.", small_pdf())):
            def invalid(args, **kwargs):
                result = self.fake_engine(args, **kwargs)
                if args[-1] == "document.tex":
                    output = Path(kwargs["cwd"]) / "output"
                    (output / "document.pdf").write_bytes(data)
                    (output / "document.log").write_text(log, encoding="utf-8")
                return result
            with engine_process(invalid), redirect_stdout(io.StringIO()):
                with self.assertRaisesRegex(ValueError, "recompile"):
                    pdf.compile_document(self.root, self.key, Path(sys.executable))
            self.assertFalse(self.cached.exists())
            self.assertFalse(self.manifest_path.exists())

    def test_failed_copy_does_not_overwrite_an_existing_destination(self):
        self.compile()
        self.assets.mkdir()
        destination = self.assets / "document.pdf"
        destination.write_bytes(b"existing destination")
        self.source.write_bytes(self.source.read_bytes() + b"% stale\n")
        with self.assertRaisesRegex(ValueError, "recompile"):
            pdf.copy_verified_pdf(self.root, self.key, self.assets)
        self.assertEqual(destination.read_bytes(), b"existing destination")

    def test_non_png_source_image_is_refused_before_compilation(self):
        self.image.write_bytes(b"not a PNG")
        with engine_process(unexpected_engine), self.assertRaisesRegex(ValueError, "recompile"):
            pdf.compile_document(self.root, self.key, Path(sys.executable))
        self.assertFalse(self.cached.exists())

    def test_hardlinked_cache_source_and_destination_are_refused(self):
        self.compile()
        for target in (self.cached, self.source):
            alias = self.root / "alias"
            os.link(target, alias)
            self.refused_copy()
            alias.unlink()
        self.assets.mkdir()
        original = self.root / "untouched"
        original.write_bytes(b"untouched")
        os.link(original, self.assets / "document.pdf")
        with self.assertRaisesRegex(ValueError, "recompile"):
            pdf.copy_verified_pdf(self.root, self.key, self.assets)
        self.assertEqual(original.read_bytes(), b"untouched")

    def test_native_symlinked_parent_is_refused(self):
        self.compile()
        linked = self.root / "linked"
        try:
            linked.symlink_to(self.cached.parent, target_is_directory=True)
        except OSError:
            self.skipTest("Windows account cannot create native symlinks")
        with self.assertRaises(ValueError):
            pdf._safe_path(linked / self.cached.name)

    def test_link_and_junction_checks_are_not_dependent_on_windows_privilege(self):
        self.compile()
        for method in ("is_symlink", "is_junction"):
            original = getattr(Path, method)
            with patch.object(Path, method, lambda p: p == self.cached.parent or original(p)):
                self.refused_copy()

    def test_asset_destination_cannot_overlap_raw_or_canonical_inputs(self):
        self.compile()
        for relative in ("WKRPT400", "LiamMcGrath_Resume", "notebook_sources/sports", "tex_images/sports", pdf.CACHE):
            with self.assertRaisesRegex(ValueError, "recompile"):
                pdf.copy_verified_pdf(self.root, self.key, self.root / relative)
            self.assertFalse((self.root / relative / "document.pdf").exists())


class PublicStagingTests(unittest.TestCase):
    def test_real_report_stage_is_exactly_public_article_and_seven_pngs(self):
        from site_content.work_report import _assert_public, _private_values
        with tempfile.TemporaryDirectory() as temporary:
            stage = Path(temporary) / "stage"
            inputs = pdf._stage(ROOT, "work-term-report", stage)
            files = [p for p in stage.rglob("*") if p.is_file()]
            self.assertEqual(len(files), 8)
            self.assertEqual(len(inputs["images"]), 7)
            self.assertEqual({p.name for p in files}, {"document.tex", *[i["archive"] for i in inputs["images"]]})
            self.assertFalse({"main.tex", "gls.tex", "ece.cls"} & {p.name for p in files})
            private = _private_values((ROOT / "WKRPT400/main.tex").read_text(encoding="utf-8-sig"))
            _assert_public([p.read_bytes() for p in files] + [json.dumps(inputs)], private)

    def test_missing_original_report_is_not_bypassed_by_public_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / pdf.DOCUMENTS["work-term-report"]
            source.parent.mkdir(parents=True)
            shutil.copy2(ROOT / pdf.DOCUMENTS["work-term-report"], source)
            shutil.copy2(ROOT / "notebook_sources/work-report/manifest.json", source.parent / "manifest.json")
            with self.assertRaises(FileNotFoundError):
                pdf._stage(root, "work-term-report", root / "stage")

    def test_import_is_stdlib_only_and_performs_no_compiler_or_publisher_import(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = subprocess.run([sys.executable, "-B", "-S", "-c",
                "import sys; import site_content.pdf; "
                "assert 'site_content.publishing' not in sys.modules; "
                "assert 'site_content.work_report' not in sys.modules"],
                cwd=temporary, env={**os.environ, "PYTHONPATH": str(ROOT)}, capture_output=True, check=True)
            self.assertEqual(result.stdout + result.stderr, b"")
            self.assertEqual(list(Path(temporary).iterdir()), [])

    def test_cli_choices_root_and_explicit_engine(self):
        with patch.object(pdf, "compile_document", return_value={"bytes": 123, "sha256": "fixture"}) as compile_one, \
                redirect_stdout(io.StringIO()):
            pdf.main(["--root", str(ROOT), "--engine", "fixture-engine", "--document", "creator-pitch"])
            compile_one.assert_called_once_with(ROOT, "creator-pitch", Path("fixture-engine"))
            compile_one.reset_mock()
            pdf.main(["--root", str(ROOT), "--engine", "fixture-engine"])
            self.assertEqual([call.args[1] for call in compile_one.call_args_list], list(pdf.DOCUMENTS))


if __name__ == "__main__":
    unittest.main()