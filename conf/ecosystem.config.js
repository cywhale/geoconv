module.exports = {
  apps : [{
    name: 'geoconv',
    script: 'gunicorn src.geoconv_app:app -w 1 -k uvicorn.workers.UvicornWorker -b 127.0.0.1:8015 --keyfile conf/privkey.pem --certfile conf/fullchain.pem --reload',
    args: '',
    merge_logs: true,
    autorestart: true,
    log_file: "tmp/combined.geoconv.log",
    out_file: "tmp/geoconv.log",
    error_file: "tmp/geoconv_err.log",
    log_date_format : "YYYY-MM-DD HH:mm Z",
    append_env_to_name: true,
    watch: false,
    max_memory_restart: '8G',
  }],
};

