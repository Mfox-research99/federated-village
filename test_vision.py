#!/usr/bin/env python3
"""
Quick smoke test for mlx-vlm vision models.
Usage:
  python test_vision.py --model gemma     # test Gemma 4 E4B
  python test_vision.py --model qwen      # test Qwen2.5-VL 7B
  python test_vision.py --model both      # test both sequentially
  python test_vision.py --image /path/to/image.jpg  # use a specific image
"""

import argparse
import sys
from pathlib import Path

MODELS = {
    "gemma": {
        "path": "/Users/michaeldavis/models/gemma-4-e4b-it-mlx-4bit",
        "label": "Gemma 4 E4B (MLX 4-bit)",
    },
    "qwen": {
        "path": "/Users/michaeldavis/models/Qwen2.5-VL-7B-Instruct-mlx-4bit",
        "label": "Qwen2.5-VL 7B (MLX 4-bit)",
    },
}

# Default test: describe this image (a simple public-domain chart or screenshot)
DEFAULT_PROMPT = (
    "Describe what you see in this image. Be specific about any text, "
    "charts, maps, or visual data present."
)

# Fallback: text-only test if no image provided
TEXT_ONLY_PROMPT = (
    "What is the Seventh Generation principle, and how does it apply "
    "to long-horizon policy decisions? Answer in 3-4 sentences."
)


def test_model(model_key: str, image_path: str | None, prompt: str):
    from mlx_vlm import load, generate
    from mlx_vlm.prompt_utils import apply_chat_template
    from mlx_vlm.utils import load_config

    cfg = MODELS[model_key]
    print(f"\n{'='*60}")
    print(f"Testing: {cfg['label']}")
    print(f"Path: {cfg['path']}")
    if not Path(cfg["path"]).exists():
        print(f"  ERROR: Model not found at {cfg['path']}")
        print(f"  Run the download first (see mlx-vlm setup in tooling-registry.md)")
        return

    print(f"Loading model...")
    model, processor = load(cfg["path"])
    config = load_config(cfg["path"])

    if image_path:
        print(f"Image: {image_path}")
        messages = [{"role": "user", "content": prompt}]
        formatted = apply_chat_template(processor, config, prompt, num_images=1)
        output = generate(model, processor, formatted, image=image_path, max_tokens=512, verbose=False)
    else:
        print("No image provided — text-only test")
        messages = [{"role": "user", "content": TEXT_ONLY_PROMPT}]
        formatted = apply_chat_template(processor, config, TEXT_ONLY_PROMPT, num_images=0)
        output = generate(model, processor, formatted, max_tokens=256, verbose=False)

    print(f"\n--- Response ---")
    print(output)
    print(f"--- End ---\n")


def main():
    parser = argparse.ArgumentParser(description="mlx-vlm vision model smoke test")
    parser.add_argument("--model", choices=["gemma", "qwen", "both"], default="both",
                        help="Which model to test")
    parser.add_argument("--image", type=str, default=None,
                        help="Path to image file for vision test")
    parser.add_argument("--prompt", type=str, default=DEFAULT_PROMPT,
                        help="Prompt to use (when --image is set)")
    args = parser.parse_args()

    targets = ["gemma", "qwen"] if args.model == "both" else [args.model]
    for t in targets:
        test_model(t, args.image, args.prompt)


if __name__ == "__main__":
    main()
