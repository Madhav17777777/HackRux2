# Memory-Optimized LLM Query System - Deployment Guide

## Memory Issues Fixed

The original application was exceeding Render's 512MB memory limit due to:

1. **Sentence Transformer Model**: Loading `all-MiniLM-L6-v2` on every request
2. **Large PDF Processing**: Loading entire PDFs into memory
3. **FAISS Index**: Storing embeddings without cleanup
4. **No Memory Management**: Data persisting between requests

## Optimizations Implemented

### 1. Lazy Loading

- Models are loaded only when first needed
- Memory is freed after each request
- Batch processing for large documents

### 2. Memory Limits

- PDF pages limited to 30 (configurable via `MAX_PDF_PAGES`)
- Questions limited to 5 per request (configurable via `MAX_QUESTIONS`)
- Memory usage capped at 400MB (configurable via `MEMORY_LIMIT_MB`)

### 3. Garbage Collection

- Forced cleanup after each processing step
- Memory monitoring and logging
- Automatic cleanup on errors

### 4. Batch Processing

- PDF processing in 10-page batches
- Embedding generation in 50-chunk batches
- Progressive memory cleanup

## Deployment on Render

### Method 1: Using render.yaml (Recommended)

1. Push your code to GitHub
2. Connect your repository to Render
3. Render will automatically detect the `render.yaml` file
4. The service will be deployed with optimized settings

### Method 2: Manual Configuration

1. **Environment Variables**:

   ```
   MAX_PDF_PAGES=30
   MAX_QUESTIONS=5
   MEMORY_LIMIT_MB=400
   PYTHONHASHSEED=random
   PYTHONDONTWRITEBYTECODE=1
   ```

2. **Build Command**:

   ```
   pip install -r requirements.txt
   ```

3. **Start Command**:

   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
   ```

4. **Health Check Path**:
   ```
   /health
   ```

## Monitoring Memory Usage

### Health Check Endpoint

```
GET /health
```

Returns current memory usage and system status.

### Memory Status Endpoint

```
GET /memory
```

Returns detailed memory information including:

- RSS (Resident Set Size) in MB
- VMS (Virtual Memory Size) in MB
- Memory usage percentage
- Available system memory
- Whether within memory limits

## Configuration Options

### Environment Variables

| Variable          | Default | Description                   |
| ----------------- | ------- | ----------------------------- |
| `MAX_PDF_PAGES`   | 50      | Maximum PDF pages to process  |
| `MAX_QUESTIONS`   | 10      | Maximum questions per request |
| `MEMORY_LIMIT_MB` | 400     | Memory limit in MB            |
| `GEMINI_API_KEY`  | -       | Required: Your Gemini API key |

### Memory Optimization Settings

- **Garbage Collection**: Aggressive cleanup after each step
- **Batch Processing**: Limits concurrent memory usage
- **Lazy Loading**: Models loaded only when needed
- **Memory Monitoring**: Real-time tracking and limits

## Troubleshooting

### Memory Still Exceeding Limits

1. **Reduce PDF Page Limit**:

   ```bash
   MAX_PDF_PAGES=20
   ```

2. **Reduce Question Limit**:

   ```bash
   MAX_QUESTIONS=3
   ```

3. **Lower Memory Limit**:
   ```bash
   MEMORY_LIMIT_MB=350
   ```

### Performance Issues

1. **Check Memory Usage**:

   ```bash
   curl https://your-app.onrender.com/memory
   ```

2. **Monitor Health**:

   ```bash
   curl https://your-app.onrender.com/health
   ```

3. **Review Logs**: Check Render logs for memory usage patterns

## Expected Memory Usage

- **Base Memory**: ~150-200MB (Python + FastAPI)
- **Model Loading**: +50-80MB (Sentence Transformer)
- **PDF Processing**: +20-50MB per 10 pages
- **Embedding Generation**: +30-60MB during processing
- **Total Peak**: ~350-400MB (within Render's 512MB limit)

## Best Practices

1. **Monitor Regularly**: Use the `/memory` endpoint to track usage
2. **Set Appropriate Limits**: Adjust based on your use case
3. **Handle Large PDFs**: Consider splitting very large documents
4. **Optimize Questions**: Batch related questions together
5. **Use Health Checks**: Monitor application health

## Support

If you continue to experience memory issues:

1. Check the `/memory` endpoint for current usage
2. Review application logs for memory patterns
3. Consider upgrading to a higher-tier Render plan
4. Implement document preprocessing to reduce size
