/* Batch driver. HB_BATCH_JOBS/HB_FINALIZE_SCRIPT_PATH/HB_BATCH_REPORT_PATH are injected. */
(function () {
    function jsonStringify(value) {
        if (value === null) { return "null"; }
        if (typeof value === "string") {
            var escaped = "";
            for (var ci = 0; ci < value.length; ci += 1) {
                var character = value.charAt(ci);
                var code = value.charCodeAt(ci);
                if (character === "\\") { escaped += "\\\\"; }
                else if (character === '"') { escaped += '\\"'; }
                else if (character === "\r") { escaped += "\\r"; }
                else if (character === "\n") { escaped += "\\n"; }
                else if (character === "\t") { escaped += "\\t"; }
                else if (code < 32) {
                    escaped += "\\u00" + (code < 16 ? "0" : "") + code.toString(16);
                } else { escaped += character; }
            }
            return '"' + escaped + '"';
        }
        if (typeof value === "number" || typeof value === "boolean") {
            return String(value);
        }
        if (value instanceof Array) {
            var items = [];
            for (var ai = 0; ai < value.length; ai += 1) {
                items.push(jsonStringify(value[ai]));
            }
            return "[" + items.join(",") + "]";
        }
        var fields = [];
        for (var key in value) {
            if (value.hasOwnProperty(key)) {
                fields.push(jsonStringify(key) + ":" + jsonStringify(value[key]));
            }
        }
        return "{" + fields.join(",") + "}";
    }

    function writeJson(path, value) {
        var file = File(path);
        file.parent.create();
        file.encoding = "UTF-8";
        if (!file.open("w")) { throw Error("cannot write batch report: " + path); }
        file.write(jsonStringify(value));
        file.write("\n");
        file.close();
    }

    var batch = {
        schema_version: "indesign-finalize-jsx-batch/v1",
        success: true,
        jobs: []
    };
    for (var ji = 0; ji < HB_BATCH_JOBS.length; ji += 1) {
        var job = HB_BATCH_JOBS[ji];
        var result = {
            job_id: String(job.job_id || ""),
            job_path: String(job.job_path || ""),
            report_json: String(job.report_json || ""),
            completed: false,
            error: null
        };
        try {
            $.global.HB_JOB_PATH = result.job_path;
            $.evalFile(File(HB_FINALIZE_SCRIPT_PATH));
            result.completed = File(result.report_json).exists;
            if (!result.completed) {
                result.error = "finalize script returned without writing its report";
            }
        } catch (error) {
            result.error = String(error) + (error.line ? " at line " + error.line : "");
        }
        if (!result.completed) { batch.success = false; }
        batch.jobs.push(result);
    }
    writeJson(HB_BATCH_REPORT_PATH, batch);
}());
