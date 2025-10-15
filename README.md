# Python Tutor Agent

The LLM-based tutoring agent helps learners understand and debug Python code. Rather than simply fixing errors, it analyzes failed tests to generate targeted, instructional hints that build conceptual understanding. It performs adaptive reasoning by assessing the complexity of each error, selecting an appropriate tutoring strategy (conceptual clarification, guided questioning, or step-by-step prompting), and refining its responses through self-evaluation scored by an LLM-as-a-judge.

`Qwen/Qwen2.5-3B-Instruct` is LoRA fine-tuned on a custom dataset created specifically for this project. The fine-tuned model is evaluated against its base version to measure improvements in tutoring quality. Both direct inference and adaptive agent modes are tested, with each generated hint rated for pedagogical effectiveness using `GPT-4o-mini`.

## Quick Start

1. **Environment Setup**
   ```bash
   conda env create -f environment.yml
   conda activate python-tutor-agent
   ```

2. **Install PyTorch**: https://pytorch.org/get-started/locally/

3. **Pre-process the dataset**
   ```bash
   python -m data.preprocess
   ```

4. **Get model weights** (choose one):
   - **a. Train your own**: Follow `notebooks/fine-tuning.ipynb` to fine-tune with LoRA, then download `qwen2.5-3b-instruct-fine-tuned.zip` from Kaggle's output files
   - **b. Use pre-trained**: Download from [GitHub Releases](https://github.com/condainit/python-tutor-agent/releases)

5. **Extract weights**
   ```bash
   mkdir weights
   unzip qwen2.5-3b-instruct-fine-tuned.zip -d weights/
   ```

6. **Set API key for LLM-as-a-judge**
   ```bash
   # macOS/Linux:
   export OPENAI_API_KEY=YOUR_KEY
   
   # Windows (PowerShell):
   $env:OPENAI_API_KEY = "YOUR_KEY"
   ```

7. **Run evaluation**
   ```bash
   python -m eval.benchmark
   ```

## Agent Architecture

The tutoring agent takes a programming problem, learner code, and failed test results as input, then adaptively generates pedagogically appropriate hints that guide learners toward solutions without revealing answers:

1. **Analyze**: Determines error complexity (simple/moderate/complex)
2. **Plan**: Selects tutoring strategy (direct/questions/step_by_step) 
3. **Generate**: Creates strategy-aware hints using either the fine-tuned or base model
4. **Evaluate**: Self-scores hints using LLM-as-a-judge (1-5 scale)
5. **Adapt**: Tries alternative approaches if score < 4, stopping when score >= 4 or strategies exhausted

## Dataset

The dataset is derived from the [MBPP (Mostly Basic Python Problems)](https://huggingface.co/datasets/google-research-datasets/mbpp) corpus, adapted for a tutoring use case.

It contains 100 total learner attempts (80 for training, 10 for evaluation, and 10 for testing), each consisting of:
   - A Python programming problem
   - A student (buggy) solution
   - The corresponding unit tests
   - A human-written tutor hint that addresses the failure without revealing the solution

This structure allows for fine-tuning and benchmarking of models on realistic tutoring behavior.

## Evaluation

The evaluation compares five approaches to demonstrate both fine-tuning and agent reasoning benefits:

- **Human**: Human-authored hints from the dataset
- **Base**: Base model without tutoring-specific training
- **Fine-tuned**: LoRA fine-tuned model without reasoning
- **Agent (Base)**: Agent with reasoning using base model
- **Agent (Fine-tuned)**: Agent with reasoning using fine-tuned model

Each hint is scored by an LLM judge on pedagogical effectiveness (1-5 scale).

## Results

On the test split, average scores were:
- **Human**: 5.00 (human-authored pedagogical hints)
- **Base**: 3.62 (general-purpose model baseline)
- **Fine-tuned**: 4.00 (tutoring-specific training shows improvement)
- **Agent (Base)**: 4.00 (reasoning improves base model performance)
- **Agent (Fine-tuned)**: 4.00 (combined fine-tuning and reasoning)

### Key Findings

- **Fine-tuned** vs **Base**: +0.38; gains with 80 training samples
- **Agent (Base)** vs **Base**: +0.38; adaptive reasoning improves hint quality
- **Agent (Fine-tuned)** vs **Agent (Base)**: +0.00; no added benefit