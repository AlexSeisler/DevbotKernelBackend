from fastapi import APIRouter, HTTPException
from services.training.federation_data_exporter import FederationDataExporter
from services.training.architecture_pattern_analyzer import ArchitecturePatternAnalyzer
from services.training.training_payload_generator import TrainingPayloadGenerator

router = APIRouter(prefix="/training")

@router.get("/build-training-set")
async def build_training_set():
    try:
        exporter = FederationDataExporter()
        analyzer = ArchitecturePatternAnalyzer()
        generator = TrainingPayloadGenerator()

        full_graph = exporter.export_full_graph()
        if not full_graph:
            raise ValueError("Federation graph query returned no data")

        patterns = analyzer.analyze_graph(full_graph)
        payloads = generator.generate_payload(patterns)

        if not payloads:
            raise ValueError("Training payload generation returned empty result")

        output_path = "training_dataset.jsonl"
        generator.save_to_json(payloads, output_path)

        return {"status": "training_dataset_generated", "file_path": output_path}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))