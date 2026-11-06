use std::collections::BTreeMap;
use std::path::Path;

use serde_json::Value;

const BASE_POLICY: &[(&str, &[&str])] = &[
    ("default-src", &["'self'"]),
    ("script-src", &["'self'"]),
    ("style-src", &["'self'"]),
    ("font-src", &["'self'"]),
    ("img-src", &["'self'", "data:", "blob:"]),
    ("connect-src", &["'self'", "ipc:", "http://ipc.localhost"]),
    ("object-src", &["'none'"]),
    ("base-uri", &["'self'"]),
    ("form-action", &["'self'"]),
    ("frame-src", &["'none'"]),
    ("frame-ancestors", &["'none'"]),
];

const FORBIDDEN_SOURCES: &[&str] = &["'unsafe-inline'", "'unsafe-eval'", "'nonce-", "*"];

fn tauri_config() -> Value {
    let path = Path::new(env!("CARGO_MANIFEST_DIR")).join("tauri.conf.json");
    let text = std::fs::read_to_string(path).expect("tauri.conf.json is readable");
    serde_json::from_str(&text).expect("tauri.conf.json is valid JSON")
}

fn security(config: &Value) -> &Value {
    &config["app"]["security"]
}

fn sources(value: &Value) -> Vec<String> {
    match value {
        Value::String(text) => text.split_whitespace().map(str::to_owned).collect(),
        Value::Array(items) => items
            .iter()
            .map(|item| item.as_str().expect("CSP source is a string").to_owned())
            .collect(),
        other => panic!("unexpected CSP directive value: {other}"),
    }
}

fn csp_directives(config: &Value) -> BTreeMap<String, Vec<String>> {
    let csp = security(config)["csp"]
        .as_object()
        .expect("app.security.csp is a directive map");
    csp.iter()
        .map(|(name, value)| (name.clone(), sources(value)))
        .collect()
}

#[test]
fn csp_has_exactly_the_base_directives() {
    let expected: BTreeMap<String, Vec<String>> = BASE_POLICY
        .iter()
        .map(|(name, values)| {
            (
                (*name).to_owned(),
                values.iter().map(|value| (*value).to_owned()).collect(),
            )
        })
        .collect();

    assert_eq!(csp_directives(&tauri_config()), expected);
}

#[test]
fn csp_has_no_permissive_sources() {
    for (name, values) in csp_directives(&tauri_config()) {
        for value in values {
            for forbidden in FORBIDDEN_SOURCES {
                assert!(
                    !value.starts_with(forbidden),
                    "{name} contains the forbidden source {value}"
                );
            }
        }
    }
}

#[test]
fn dev_csp_is_not_declared() {
    assert!(security(&tauri_config()).get("devCsp").is_none());
}
