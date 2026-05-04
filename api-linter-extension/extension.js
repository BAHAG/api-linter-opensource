// Import the module and reference it with the alias vscode in your code below
const vscode = require('vscode');
const { spawn, spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const rules_json = path.join(__filename, '..', 'data', 'rules.json');

// Decoration types for error (red) and warning (orange) line highlights
const errorDecorationType = vscode.window.createTextEditorDecorationType({
	borderWidth: '0 0 0 3px',
	borderStyle: 'solid',
	borderColor: 'rgba(220, 50, 50, 0.9)',
	backgroundColor: 'rgba(220, 50, 50, 0.08)',
	isWholeLine: true,
});

const warningDecorationType = vscode.window.createTextEditorDecorationType({
	borderWidth: '0 0 0 3px',
	borderStyle: 'solid',
	borderColor: 'rgba(210, 120, 30, 0.9)',
	backgroundColor: 'rgba(210, 120, 30, 0.08)',
	isWholeLine: true,
});

// Create a status bar item
const myStatusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left, 200);

// Set the text and tooltip for the button
myStatusBarItem.text = "Linter"; // Replace with your preferred icon and text
myStatusBarItem.tooltip = "Lint Api Spec"; // Tooltip text

// Add a command to be executed when the button is clicked
myStatusBarItem.command = "api-linter.helloWorld"; // Replace with the actual command to trigger your extension
myStatusBarItem.show();

const lintWithApiLinter = (diagnosticCollection, new_content="", editor=null) => {
	if (!editor) editor = vscode.window.activeTextEditor;
	if (editor) {
		const document = editor.document;
		if (!editor.document.fileName.endsWith(".yaml")){
			console.log("This is not a yaml file")
			return
		}
		// get the path of the yaml file
		let filePath = document.uri.fsPath;
		const documentUri = document.uri;
		if (new_content){
			filePath = "/tmp/linter-extension.yaml"
			fs.writeFileSync(filePath, new_content)
		}
		// Check whether the native 'linting' binary is available
		const whichResult = spawnSync('which', ['linting']);
		const lintingExists = whichResult.status === 0;

		let linting;
		if (lintingExists) {
			// Native binary found – use it directly
			linting = spawn('linting', ['-s', filePath, '-r', rules_json, '-o', 'json']);
		} else {
			// Fall back to Docker
			const fileDir = path.dirname(filePath);
			const fileName = path.basename(filePath);
			linting = spawn('docker', [
				'run',
				'--platform', 'linux/amd64',
				'--rm',
				'-v', `${fileDir}:/spec`,
				'ghcr.io/bahag/api-linter-opensource:latest',
				'linting',
				'-s', `/spec/${fileName}`,
				'-r', '/rules.json',
				'-o', 'json'
			]);
		}

		linting.stderr.on('data', (data) => {
			console.log("STDERR: ", data.toString());
		});

		linting.stdout.on('data', (data) => {
			console.log("Received data: ");
		});

		linting.on("error", (error) => {
			console.log(error)
			vscode.window.showErrorMessage('Linting failed. Cannot start Child Process.');
		})

		linting.on('close', (code) => {
			if (code === 0) {
				const json_file_path = filePath.replace(".yaml", "") + "-output.json"
				const linting_data = JSON.parse(fs.readFileSync(json_file_path).toString())
				let linting_logs = linting_data["logs"];
				let diagnostics = [];

				for (let linting_result of linting_logs){
					const error_id = linting_result["id"];
					const error_message = linting_result["message"];
					const error_severity = linting_result["severity"];
					// Use num_line if available, otherwise fall back to line 1
					const line_number = linting_result["num_line"] ? linting_result["num_line"] - 1 : 0;

					const range = new vscode.Range(line_number, 0, line_number, Number.MAX_SAFE_INTEGER);
					const message = error_id ? `[${error_id}] ${error_message}` : error_message;
					const severity = error_severity === "ERROR"
						? vscode.DiagnosticSeverity.Error
						: vscode.DiagnosticSeverity.Warning;

					const diagnostic = new vscode.Diagnostic(range, message, severity);
					diagnostic.source = 'api-linter';
					if (error_id) {
						diagnostic.code = error_id;
					}
					diagnostics.push(diagnostic);
				}

				// Replace diagnostics for this document
				diagnosticCollection.delete(documentUri);
				diagnosticCollection.set(documentUri, diagnostics);

				if (!new_content){
					fs.unlinkSync(filePath.replace(".yaml", "") + "-output.json")
				}
			} else {
				vscode.window.showErrorMessage('Linting failed. Check the Problems panel for details.');
			}
		});
	}
	else{
		console.log("No active editor")
	}
};

// This method is called when your extension is activated
// Your extension is activated the very first time the command is executed
/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
	const diagnosticCollection = vscode.languages.createDiagnosticCollection('api-linter');
	context.subscriptions.push(diagnosticCollection);

	let disposable = vscode.commands.registerCommand('api-linter.helloWorld', function () {
		lintWithApiLinter(diagnosticCollection)
	});

	context.subscriptions.push(disposable);

	// Event listener for document save
    context.subscriptions.push(vscode.workspace.onDidSaveTextDocument(document => {
		lintWithApiLinter(diagnosticCollection, "")
    }));

	context.subscriptions.push(vscode.workspace.onDidChangeTextDocument(document => {
		lintWithApiLinter(diagnosticCollection, document.document.getText())
    }));

	context.subscriptions.push(vscode.window.onDidChangeActiveTextEditor(editor => {
        if (editor) {
            lintWithApiLinter(diagnosticCollection);
        }
    }));

	context.subscriptions.push(vscode.workspace.onDidOpenTextDocument(document => {
		lintWithApiLinter(diagnosticCollection, "")
	}));
}

// This method is called when your extension is deactivated
function deactivate() {}

module.exports = {
	activate,
	deactivate
}
