"""Unit tests for batch processing functions."""

import pytest
import tempfile
from pathlib import Path

from parser.batch import find_yaml_files, process_files_batch
from parser.models import BatchSummary


class TestFindYAMLFiles:
    """Tests for YAML file discovery."""

    def test_find_yaml_files_recursive(self, tmp_path):
        """Test recursive discovery of YAML files."""
        # Create directory structure with YAML files
        (tmp_path / "app1.yaml").touch()
        (tmp_path / "app2.yml").touch()
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "app3.yaml").touch()
        (tmp_path / "subdir" / "nested").mkdir()
        (tmp_path / "subdir" / "nested" / "app4.yml").touch()
        (tmp_path / "not-yaml.txt").touch()

        files = find_yaml_files(tmp_path, recursive=True)

        assert len(files) == 4
        assert all(f.suffix in [".yaml", ".yml"] for f in files)
        assert any("app1.yaml" in str(f) for f in files)
        assert any("app4.yml" in str(f) for f in files)

    def test_find_yaml_files_non_recursive(self, tmp_path):
        """Test non-recursive discovery of YAML files."""
        (tmp_path / "app1.yaml").touch()
        (tmp_path / "app2.yml").touch()
        (tmp_path / "subdir").mkdir()
        (tmp_path / "subdir" / "app3.yaml").touch()

        files = find_yaml_files(tmp_path, recursive=False)

        assert len(files) == 2
        assert all("subdir" not in str(f) for f in files)

    def test_find_yaml_files_empty_directory(self, tmp_path):
        """Test finding files in empty directory."""
        files = find_yaml_files(tmp_path, recursive=True)
        assert files == []

    def test_find_yaml_files_not_a_directory(self, tmp_path):
        """Test error when path is not a directory."""
        file_path = tmp_path / "file.yaml"
        file_path.touch()

        with pytest.raises(NotADirectoryError):
            find_yaml_files(file_path)

    def test_find_yaml_files_sorted(self, tmp_path):
        """Test that results are sorted."""
        (tmp_path / "zzz.yaml").touch()
        (tmp_path / "aaa.yaml").touch()
        (tmp_path / "mmm.yaml").touch()

        files = find_yaml_files(tmp_path)

        # Check that files are sorted
        file_names = [f.name for f in files]
        assert file_names == sorted(file_names)

    def test_find_yaml_files_no_duplicates(self, tmp_path):
        """Test that no duplicate files are returned."""
        (tmp_path / "app.yaml").touch()
        (tmp_path / "app.yml").touch()

        files = find_yaml_files(tmp_path)

        # Each unique file should appear only once
        assert len(files) == 2
        assert len(set(files)) == len(files)


class TestProcessFilesBatch:
    """Tests for batch file processing."""

    def test_process_batch_all_valid(self, tmp_path):
        """Test batch processing with all valid manifests."""
        # Create valid manifest files
        manifest1 = tmp_path / "app1.yaml"
        manifest1.write_text("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app1
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    path: ./app1
  destination:
    server: https://kubernetes.default.svc
    namespace: default
""")

        manifest2 = tmp_path / "app2.yaml"
        manifest2.write_text("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app2
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    path: ./app2
  destination:
    server: https://kubernetes.default.svc
    namespace: default
""")

        output_dir = tmp_path / "output"
        files = [manifest1, manifest2]

        summary = process_files_batch(files, output_dir, show_progress=False)

        assert summary.total == 2
        assert summary.successful == 2
        assert summary.failed == 0
        assert summary.skipped == 0
        assert summary.success_rate == 100.0
        assert len(summary.results) == 2

    def test_process_batch_mixed_valid_invalid(self, tmp_path):
        """Test batch processing with mix of valid and invalid manifests."""
        # Valid manifest
        valid_manifest = tmp_path / "valid.yaml"
        valid_manifest.write_text("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: valid-app
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    path: ./valid
  destination:
    server: https://kubernetes.default.svc
    namespace: default
""")

        # Invalid manifest (missing required fields)
        invalid_manifest = tmp_path / "invalid.yaml"
        invalid_manifest.write_text("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: invalid-app
spec:
  project: default
""")

        output_dir = tmp_path / "output"
        files = [valid_manifest, invalid_manifest]

        summary = process_files_batch(files, output_dir, show_progress=False)

        assert summary.total == 2
        assert summary.successful == 1
        assert summary.failed == 1
        assert summary.skipped == 0
        assert 40 < summary.success_rate < 60  # Should be 50%

    def test_process_batch_error_isolation(self, tmp_path):
        """Test that one invalid file doesn't stop processing of others."""
        # Create 3 manifests: valid, invalid, valid
        manifest1 = tmp_path / "app1.yaml"
        manifest1.write_text("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app1
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    path: ./app1
  destination:
    server: https://kubernetes.default.svc
    namespace: default
""")

        manifest2_invalid = tmp_path / "invalid.yaml"
        manifest2_invalid.write_text("""
apiVersion: v1
kind: Service
metadata:
  name: not-argocd
""")

        manifest3 = tmp_path / "app3.yaml"
        manifest3.write_text("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app3
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    path: ./app3
  destination:
    server: https://kubernetes.default.svc
    namespace: default
""")

        output_dir = tmp_path / "output"
        files = [manifest1, manifest2_invalid, manifest3]

        summary = process_files_batch(files, output_dir, show_progress=False)

        assert summary.total == 3
        assert summary.successful == 2
        assert summary.failed == 1
        assert output_dir.exists()
        assert (output_dir / "app1.json").exists()
        assert (output_dir / "app3.json").exists()
        assert not (output_dir / "not-argocd.json").exists()

    def test_process_batch_empty_file_list(self, tmp_path):
        """Test batch processing with empty file list."""
        output_dir = tmp_path / "output"
        files = []

        summary = process_files_batch(files, output_dir, show_progress=False)

        assert summary.total == 0
        assert summary.successful == 0
        assert summary.failed == 0
        assert summary.success_rate == 0.0

    def test_batch_summary_success_rate(self):
        """Test success rate calculation in BatchSummary."""
        from parser.models import BatchSummary

        # 100% success
        summary = BatchSummary(total=10, successful=10, failed=0)
        assert summary.success_rate == 100.0

        # 50% success
        summary = BatchSummary(total=10, successful=5, failed=5)
        assert summary.success_rate == 50.0

        # 0% success
        summary = BatchSummary(total=10, successful=0, failed=10)
        assert summary.success_rate == 0.0

        # No files processed
        summary = BatchSummary(total=0, successful=0, failed=0)
        assert summary.success_rate == 0.0

    def test_process_batch_with_config(self, tmp_path):
        """Test batch processing with cluster mappings and default labels."""
        manifest = tmp_path / "app.yaml"
        manifest.write_text("""
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: test-app
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    path: ./app
  destination:
    server: https://kubernetes.default.svc
    namespace: default
""")

        output_dir = tmp_path / "output"
        cluster_mappings = {"https://kubernetes.default.svc": "prod-cluster"}
        default_labels = {"team": "platform"}

        summary = process_files_batch(
            files=[manifest],
            output_dir=output_dir,
            cluster_mappings=cluster_mappings,
            default_labels=default_labels,
            show_progress=False,
        )

        assert summary.successful == 1

        # Verify config was applied
        import json
        output_file = output_dir / "test-app.json"
        with open(output_file) as f:
            output = json.load(f)

        assert output["destination"]["clusterName"] == "prod-cluster"
        assert output["metadata"]["labels"]["team"] == "platform"
