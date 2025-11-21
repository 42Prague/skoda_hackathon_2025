"""
Async File I/O Tests
-------------------
Test all async file operations.
"""

import pytest
import json
from pathlib import Path
from unittest.mock import patch

from swx_api.app.services.ingestion_service import (
    read_json_async,
    save_json_async,
    read_text_async,
)


class TestAsyncFileIO:
    """Test async file I/O operations."""
    
    @pytest.mark.asyncio
    async def test_read_json_async(self, temp_data_dir: Path):
        """Test async JSON reading."""
        # Create test JSON file
        json_path = temp_data_dir / "test.json"
        test_data = {"key": "value", "number": 42}
        
        with open(json_path, "w") as f:
            json.dump(test_data, f)
        
        # Read asynchronously
        result = await read_json_async(json_path)
        
        assert result == test_data
        assert result["key"] == "value"
        assert result["number"] == 42
    
    @pytest.mark.asyncio
    async def test_save_json_async(self, temp_data_dir: Path):
        """Test async JSON writing."""
        json_path = temp_data_dir / "output.json"
        test_data = {"test": "data", "count": 100}
        
        # Write asynchronously
        await save_json_async(json_path, test_data)
        
        # Verify file was created and contains correct data
        assert json_path.exists()
        
        with open(json_path, "r") as f:
            loaded = json.load(f)
        
        assert loaded == test_data
        assert loaded["test"] == "data"
    
    @pytest.mark.asyncio
    async def test_read_text_async(self, temp_data_dir: Path):
        """Test async text reading."""
        text_path = temp_data_dir / "test.txt"
        test_content = "This is test content\nWith multiple lines"
        
        with open(text_path, "w") as f:
            f.write(test_content)
        
        # Read asynchronously
        result = await read_text_async(text_path)
        
        assert result == test_content
        assert "test content" in result
    
    @pytest.mark.asyncio
    async def test_ingest_file_async(self, temp_data_dir: Path):
        """Test async file ingestion."""
        import pandas as pd
        from swx_api.app.services.ingestion_service import ingest_file
        
        # Create test CSV
        csv_path = temp_data_dir / "test.csv"
        df = pd.DataFrame({
            "employee_id": ["EMP001", "EMP002"],
            "department": ["Engineering", "Sales"],
            "skills": ["Python", "JavaScript"],
        })
        df.to_csv(csv_path, index=False)
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            mock_paths.raw_dir = temp_data_dir / "raw"
            
            result = await ingest_file(csv_path, "test.csv")
            
            assert "dataset_id" in result
            assert "metadata" in result
            assert result["metadata"]["row_count"] == 2
    
    @pytest.mark.asyncio
    async def test_list_datasets_async(self, temp_data_dir: Path):
        """Test async dataset listing."""
        from swx_api.app.services.ingestion_service import list_datasets
        import pandas as pd
        
        # Create test datasets
        csv1 = temp_data_dir / "normalized" / "dataset1.csv"
        csv2 = temp_data_dir / "normalized" / "dataset2.csv"
        
        df = pd.DataFrame({"col1": [1, 2, 3]})
        df.to_csv(csv1, index=False)
        df.to_csv(csv2, index=False)
        
        with patch("swx_api.app.services.ingestion_service.paths") as mock_paths:
            mock_paths.normalized_dir = temp_data_dir / "normalized"
            mock_paths.processed_dir = temp_data_dir / "processed"
            
            datasets = await list_datasets()
            
            assert len(datasets) >= 2
            dataset_ids = [d["dataset_id"] for d in datasets]
            assert "dataset1" in dataset_ids or "dataset2" in dataset_ids

