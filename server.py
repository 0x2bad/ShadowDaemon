from flask import Flask, request, jsonify
from string import Template
import argparse
import datetime
import logging
import os

# Configure logging
logger = logging.getLogger('binary_server')
logger.setLevel(logging.INFO)

app = Flask(__name__)

# Silence Werkzeug logs
werkzeug_log = logging.getLogger('werkzeug')
werkzeug_log.setLevel(logging.ERROR)

@app.route('/<path:path>', methods=['GET', 'POST'])
def catch_all(path):
    client_ip = request.remote_addr
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check if this is a binary request
    if request.headers.get('X-Request-Type') == 'binary':
        try:
            # Verify the path is safe and exists
            if '..' in path or path.startswith('/'):
                logger.warning(f"[{timestamp}] IP: {client_ip} - Invalid path attempted: {path}")
                return jsonify({"error": "Invalid path"}), 400
                
            binary_path = os.path.join(app.config['bin_dir'], path)
            
            if not os.path.exists(binary_path):
                logger.error(f"Binary not found: {binary_path}")
                return jsonify({"error": f"Binary not found: {path}"}), 404
                
            # Serve the binary
            with open(binary_path, 'rb') as f:
                binary = f.read()
            return binary
        except Exception as e:
            logger.error(f"Error serving binary {path}: {e}")
            return jsonify({"error": str(e)}), 500
    else:
        values = {
            'HOST': request.host,
            'PATH': path,
            'ARGS': request.form.get('args', ''),
        }
        
        try:
            modified_loader = app.config['loader_template'].substitute(values)
            logger.info(f"IP: {client_ip} - Command: {values['PATH']} {values['ARGS']}")
            return modified_loader
        except KeyError as e:
            logger.error(f"Missing template variable: {e}")
            return jsonify({"error": f"Template error: missing {e}"}), 500
        except Exception as e:
            logger.error(f"Template error: {e}")
            return jsonify({"error": "Failed to process template"}), 500

def main():
    parser = argparse.ArgumentParser(description="Simple binary loader server")
    parser.add_argument('--host', type=str, default='0.0.0.0', help="Host to listen on")
    parser.add_argument('--port', type=int, default=8000, help="Port to listen on")
    parser.add_argument('--debug', action='store_true', help="Enable debug mode")
    parser.add_argument('--loader', type=str, default='loader.py', help="Path to the loader script")
    parser.add_argument('--bin-dir', type=str, default='/bin', help="Directory to serve binaries from")
    parser.add_argument('--log', type=str, help="Log file path")
    args = parser.parse_args()
    
    app.config.update(vars(args))
    
    if args.log:
        file_handler = logging.FileHandler(args.log)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)
    
    print(f"Serving binaries from: {args.bin_dir}")
    print(f"Using loader template: {args.loader}")
    print(f"Listening on {args.host}:{args.port}")
    
    try:
        with open(args.loader, 'r') as f:
            app.config['loader_template'] = Template(f.read())
        logger.info(f"Successfully loaded template: {args.loader}")
    except Exception as e:
        logger.error(f"Failed to load template: {e}")
        os._exit(1)

    app.run(host=args.host, port=args.port, debug=args.debug)
    

if __name__ == '__main__':
    main()