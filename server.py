# 服务端代码，依赖flask库，用于接收上传的文件，并提供下载接口，你可以用它进行私有化部署，防止内部代码泄露。
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
        # 假设文件名格式为 "package_name-version.cpack"
        try:
            # 分割文件名
            parts = file.split('-')
            package_name = parts[0]
            
            # 存储完整的文件名
            if package_name not in packages:
                packages[package_name] = []
            if file not in packages[package_name]:
                packages[package_name].append(file)
        except (ValueError, IndexError):
            # 如果文件名格式不符合预期，跳过该文件
            continue

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
    if file.filename not in packages[package_name]:
        packages[package_name].append(file.filename)

    return jsonify({'message': '文件上传成功'}), 200

@app.route('/download/<package_name>/<version>/<filename>', methods=['GET'])
def download_file(package_name, version, filename):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        if version == filename.split('-')[1].split('.cpack')[0]:
            if package_name == filename.split('-')[0]:
                return send_file(file_path, as_attachment=True)
            else:
                return jsonify({'error': '文件不存在'}), 400
        else:
            return jsonify({'error': '文件不存在'}), 400
    else:
        return jsonify({'error': '文件不存在'}), 404

@app.route('/cip/packages', methods=['GET'])
def list_packages():
    return jsonify(packages), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
