# Phase: Auto-Detect

## Overview

This phase implements automatic polygon detection capabilities for PolygonTool v2.

## Goals

- Provide multiple detection modes (basic, perfect, enhanced)
- Integrate with existing scene management
- Support various image processing algorithms
- Maintain performance and accuracy

## Architecture

### Core Components

1. **auto_detect.py**: High-level detection interface
2. **mask_utils.py**: Mask processing and contour extraction
3. **edge_utils.py**: Edge detection algorithms

### Detection Modes

- **Basic**: Simple thresholding and contour detection
- **Perfect**: Advanced algorithms with refinement
- **Enhanced**: ML-based detection (future)

### Integration Points

- Scene object creation
- CommandManager integration
- UI feedback and progress

## Implementation Plan

1. Implement basic mask processing
2. Add edge detection wrappers
3. Create high-level detection functions
4. Integrate with scene management
5. Add UI controls and feedback

## Testing

- Unit tests for each utility function
- Integration tests with scene objects
- Performance benchmarks
- Accuracy validation

## Performance Benchmarks

### Benchmarking Harness

The `bench/auto_detect_bench.py` script provides comprehensive performance testing:

- **Synthetic Test Images**: Circle, rectangle, star, multi-objects, noisy shapes
- **Metrics**: Median runtime (5 runs), polygon count, vertex count, area coverage, IoU accuracy
- **Output**: CSV results and formatted performance table

### Performance Results

| Image | Mode | Runtime (s) | Polygons | Vertices | Area | IoU |
|-------|------|-------------|----------|----------|------|-----|
| circle | Basic | 0.001 | 1 | 14 | 2838 | 0.968 |
| circle | Perfect | 0.004 | 1 | 5 | 2570 | 0.606 |
| circle | Enhanced | 0.000 | 1 | 168 | 2736 | 0.967 |
| rectangle | Basic | 0.000 | 1 | 6 | 3710 | 0.977 |
| rectangle | Perfect | 0.006 | 1 | 5 | 3364 | 0.936 |
| rectangle | Enhanced | 0.000 | 1 | 240 | 3600 | 1.000 |
| star | Basic | 0.001 | 1 | 13 | 2547 | 0.924 |
| star | Perfect | 0.005 | 1 | 7 | 2169 | 0.726 |
| star | Enhanced | 0.000 | 1 | 237 | 2399 | 1.000 |
| multi_objects | Basic | 0.001 | 3 | 27 | 4916 | N/A |
| multi_objects | Perfect | 0.008 | 3 | 15 | 4286 | N/A |
| multi_objects | Enhanced | 0.001 | 3 | 412 | 4690 | N/A |
| noisy_circle | Basic | 0.001 | 1 | 10 | 1987 | 0.946 |
| noisy_circle | Perfect | 0.003 | 1 | 5 | 1890 | 0.648 |
| noisy_circle | Enhanced | 0.001 | 1 | 396 | 9800 | 0.201 |

### Performance Insights

- **Basic Mode**: ~0.001s, fast thresholding-based detection, good for simple shapes
- **Perfect Mode**: ~0.005s, balanced performance with refinement algorithms
- **Enhanced Mode**: ~0.000-0.001s, high-fidelity with smoothing (note: vertex count increases significantly due to Chaikin smoothing)
- **Accuracy**: Basic and Enhanced modes generally provide better IoU than Perfect mode
- **Scaling**: Performance remains fast even for complex multi-object scenes
- **Trade-offs**: Enhanced mode provides highest quality but may over-smooth simple shapes