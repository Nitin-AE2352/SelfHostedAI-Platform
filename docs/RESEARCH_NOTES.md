# Research checklist

- [ ] Define whether 300 means connected users or simultaneous generations.
- [ ] Select model and target answer length.
- [ ] Compare Ollama and vLLM on chosen hardware.
- [ ] Estimate VRAM for weights, context/KV cache, and runtime overhead.
- [ ] Compare cloud hourly rental against always-on deployment.
- [ ] Decide document formats and access-control rules.
- [ ] Define target latency, throughput, and error rate.
- [ ] Benchmark gradually: 10, 25, 50, 100, 300 clients.
- [ ] Record model, GPU, VRAM, time-to-first-token, tokens/sec, queue wait,
      p50/p95 latency, and error rate.
