from flask import Flask, request, jsonify, send_file
import os

app = Flask(__name__)

# 定义上传目录
UPLOAD_FOLDER = './uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 加载已有包列表
packages = {}
for file in os.listdir(UPLOAD_FOLDER):
    if os.path.isfile(os.path.join(UPLOAD_FOLDER, file)):
        package_name, package_version = file.split('-')
        if package_name not in packages:
            packages[package_name] = []
        packages[package_name].append(f"{file}")

@app.route('/cip/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': '没有文件上传'}), 400
    
    file = request.files['file']
    package_name = request.form.get('package_name')
    package_version = request.form.get('package_version')

    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400

    # 保存文件
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)

    # 更新包列表
    if package_name not in packages:
        packages[package_name] = []
    packages[package_name].append(package_version)

    return jsonify({'message': '文件上传成功'}), 200

@app.route('/download/<package_name>/<version>/<filename>', methods=['GET'])
def download_file(package_name, version, filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': '文件不存在'}), 404

@app.route('/cip/packages', methods=['GET'])
def list_packages():
    return jsonify(packages), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
