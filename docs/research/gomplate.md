# Gomplate: Comprehensive Deep Research

## Executive Summary

Gomplate is a flexible, powerful command-line tool for template rendering written in Go. Created and maintained by Dave Henderson (hairyhenderson), it extends Go's standard `text/template` library with over 200 additional functions and supports a wide variety of datasources including JSON, YAML, AWS services, HashiCorp Consul, HashiCorp Vault, and more. It serves as a sophisticated alternative to simple tools like `envsubst` while remaining lightweight (single binary) and highly portable.

---

## Table of Contents

1. [Overview & Core Concepts](#overview--core-concepts)
2. [Installation Methods](#installation-methods)
3. [Syntax & Template Basics](#syntax--template-basics)
4. [Datasources](#datasources)
5. [Function Categories](#function-categories)
6. [Use Cases & Patterns](#use-cases--patterns)
7. [Integration with DevOps Tools](#integration-with-devops-tools)
8. [Configuration Options](#configuration-options)
9. [Best Practices](#best-practices)
10. [Comparison with Alternatives](#comparison-with-alternatives)
11. [Version History & Breaking Changes](#version-history--breaking-changes)

---

## Overview & Core Concepts

### What is Gomplate?

Gomplate is a template renderer that processes Go templates and outputs the result. At its core, it:

- Reads templates from files, stdin, or inline strings
- Pulls data from various datasources (files, APIs, secret stores, etc.)
- Renders output using Go's text/template syntax enhanced with 200+ custom functions
- Outputs to files, stdout, or multiple destinations

### Why Gomplate?

**The Problem with `envsubst`:**
- All-or-nothing variable substitution
- Limited to shell-like `$VARIABLE` syntax
- No conditional logic or data manipulation
- No support for external datasources

**Gomplate's Solution:**
- Full Go template syntax with conditionals, loops, and pipelines
- Extensive function library for data manipulation
- Support for 12+ different datasource types
- Single static binary with no dependencies

### Basic Example

```bash
# Simple environment variable substitution
$ echo 'Hello, {{ .Env.USER }}' | gomplate
Hello, dave

# Math operations
$ gomplate -i 'the answer is: {{ mul 6 7 }}'
the answer is: 42

# Using datasources
$ cat config.yaml
foo:
  bar:
    baz: qux

$ gomplate -d config=./config.yaml -i 'Value: {{ (datasource "config").foo.bar.baz }}'
Value: qux
```

---

## Installation Methods

### Package Managers

| Platform | Command |
|----------|---------|
| **macOS/Linux (Homebrew)** | `brew install gomplate` |
| **macOS (MacPorts)** | `sudo port install gomplate` |
| **Windows (Chocolatey)** | `choco install gomplate` |
| **Alpine Linux** | `apk add gomplate` |
| **Node.js (npm)** | `npm install -g gomplate` |

### Direct Download

```bash
# Linux/macOS
curl -o /usr/local/bin/gomplate -sSL https://github.com/hairyhenderson/gomplate/releases/download/v4.3.3/gomplate_linux-amd64
chmod 755 /usr/local/bin/gomplate

# Verify installation
gomplate --version
```

### Docker

```bash
# Run directly
docker run hairyhenderson/gomplate:stable --version

# Create shell alias for convenience
alias gomplate='docker run hairyhenderson/gomplate:stable'

# Use in Docker multi-stage builds
FROM alpine
COPY --from=hairyhenderson/gomplate:stable /gomplate /bin/gomplate
```

### Go Install

```bash
go install github.com/hairyhenderson/gomplate/v4/cmd/gomplate@latest
```

---

## Syntax & Template Basics

### Core Syntax

Gomplate uses Go's `text/template` syntax with actions delimited by `{{` and `}}`:

```
Hello, {{ print "World" }}!
```

### Whitespace Control

Use `-` to trim whitespace:
- `{{-` trims whitespace before the action
- `-}}` trims whitespace after the action

```go
{{- range coll.Slice "Foo" "bar" "baz" -}}
Hello, {{ . }}!
{{- end -}}
```

### Variables

```go
{{ $name := "Dave" }}
Hello, {{ $name }}!

# Variable assignment from datasource
{{ $config := datasource "config" }}
Database: {{ $config.db.host }}
```

### Control Flow

**Conditionals:**
```go
{{ if eq .Env.ENV "production" }}
  Production settings
{{ else if eq .Env.ENV "staging" }}
  Staging settings
{{ else }}
  Development settings
{{ end }}
```

**Loops:**
```go
{{ range $i, $item := (datasource "items").list }}
  {{ add 1 $i }}. {{ $item.name }}
{{ end }}
```

### Pipelines

```go
# Chain functions with |
{{ "hello world" | strings.ToUpper | strings.TrimSpace }}
# Output: HELLO WORLD

# Multiple transformations
{{ .value | conv.ToInt | mul 2 | printf "%d items" }}
```

### The Context

- `.` (dot) represents the current context
- `.Env` provides access to environment variables
- `$` always refers to the root context

```go
{{ with "foo" }}
  Context is: {{ . }}
  User is still: {{ $.Env.USER }}
{{ end }}
```

---

## Datasources

Datasources are defined with URLs and can be referenced in templates. They support lazy loading and multiple formats.

### Supported Datasources

| Type | Scheme(s) | Description |
|------|-----------|-------------|
| **File** | `file://` or relative path | Local files in JSON, YAML, TOML, CSV, or ENV format |
| **Environment** | `env:` | Environment variables |
| **HTTP/HTTPS** | `http://`, `https://` | Remote HTTP endpoints |
| **Stdin** | `stdin:` | Standard input |
| **AWS Systems Manager Parameter Store** | `aws+smp:` | Hierarchical key/value store with encrypted secrets |
| **AWS Secrets Manager** | `aws+sm:` | AWS secret storage service |
| **Amazon S3** | `s3://` | S3 object storage |
| **HashiCorp Consul** | `consul://`, `consul+https://` | Consul KV store |
| **HashiCorp Vault** | `vault://`, `vault+https://` | Vault secrets engine |
| **Google Cloud Storage** | `gs://` | GCS object storage |
| **Git** | `git://`, `git+ssh://`, `git+https://` | Files from git repositories |
| **Merge** | `merge:` | Merge multiple datasources |

### MIME Types & File Formats

| Format | MIME Type | Extensions |
|--------|-----------|------------|
| JSON | `application/json` | `.json` |
| YAML | `application/yaml` | `.yml`, `.yaml` |
| TOML | `application/toml` | `.toml` |
| CSV | `text/csv` | `.csv` |
| Plain Text | `text/plain` | - |
| ENV | `application/x-env` | `.env` |

### Datasource Examples

**File Datasource:**
```bash
# JSON file
gomplate -d config=./config.json -i '{{ (ds "config").database.host }}'

# YAML with explicit alias
gomplate -d mydata=file:///path/to/data.yaml -i '{{ (ds "mydata").key }}'
```

**Environment Datasource:**
```bash
export CONFIG='{"debug": true}'
gomplate -d cfg=env:///CONFIG?type=application/json -i '{{ (ds "cfg").debug }}'
```

**HTTP Datasource:**
```bash
gomplate -d ip=https://ipinfo.io -i 'Country: {{ (ds "ip").country }}'
```

**Vault Datasource:**
```bash
export VAULT_ADDR=https://vault.example.com
export VAULT_TOKEN=s.xxxxx
gomplate -d vault=vault:///secret/myapp -i 'Password: {{ (ds "vault").password }}'
```

**Consul Datasource:**
```bash
export CONSUL_HTTP_ADDR=localhost:8500
gomplate -d consul=consul:///config/myapp -i '{{ (ds "consul").setting }}'
```

**AWS Parameter Store:**
```bash
gomplate -d params=aws+smp:///myapp/config -i '{{ (ds "params").Value }}'
```

**Merged Datasources:**
```bash
# Merge defaults with overrides (left values override right)
gomplate -d "config=merge:./overrides.yaml|./defaults.yaml" \
         -i '{{ (ds "config").setting }}'
```

**Directory Datasources:**
```bash
# List files in a directory
gomplate -d files=./configs/ -i '{{ range ds "files" }}{{ . }}{{ end }}'
```

---

## Function Categories

Gomplate provides over 200 functions organized into namespaces:

### 1. AWS Functions (`aws.`)
- `aws.EC2Meta` - EC2 instance metadata
- `aws.EC2Region` - Current EC2 region
- `aws.EC2Tag` - EC2 instance tags
- `aws.KMSEncrypt` / `aws.KMSDecrypt` - KMS encryption
- `aws.Account` / `aws.ARN` / `aws.UserID` - AWS identity

### 2. Base64 Functions (`base64.`)
- `base64.Encode` / `base64.Decode`
- `base64.EncodeBytes` / `base64.DecodeBytes`

### 3. Collection Functions (`coll.`)
- `coll.Dict` / `dict` - Create maps
- `coll.Slice` / `slice` - Create arrays
- `coll.Has` - Check if key/value exists
- `coll.Keys` / `coll.Values` - Extract keys/values
- `coll.Merge` - Merge maps
- `coll.Sort` - Sort collections
- `coll.Flatten` - Flatten nested arrays
- `coll.Pick` / `coll.Omit` - Select/exclude keys
- `coll.JQ` - JQ-style queries

### 4. Conversion Functions (`conv.`)
- `conv.ToBool` / `conv.ToInt` / `conv.ToFloat` / `conv.ToString`
- `conv.ToInt64` / `conv.ToFloat64`
- `conv.Atoi` - String to integer
- `conv.Join` - Join array elements
- `conv.Default` - Provide default values

### 5. Crypto Functions (`crypto.`)
- `crypto.SHA1` / `crypto.SHA256` / `crypto.SHA512`
- `crypto.MD5`
- `crypto.Bcrypt`
- `crypto.PBKDF2`
- `crypto.RSAEncrypt` / `crypto.RSADecrypt`
- `crypto.ECDSAGenerateKey` - Generate ECDSA keys

### 6. Data Functions (`data.`)
- `datasource` / `ds` - Read datasource
- `include` - Include datasource content
- `defineDatasource` - Define datasource in template
- `datasourceExists` / `datasourceReachable`
- `data.JSON` / `data.YAML` / `data.TOML` / `data.CSV`
- `data.ToJSON` / `data.ToYAML` / `data.ToTOML`
- `data.JSONArray` / `data.YAMLArray`

### 7. Environment Functions (`env.`)
- `env.Getenv` / `getenv` - Get environment variable with default
- `env.ExpandEnv` - Expand `$VAR` in strings

### 8. File Functions (`file.`)
- `file.Exists` - Check file existence
- `file.IsDir` - Check if directory
- `file.Read` - Read file contents
- `file.ReadDir` - List directory contents
- `file.Stat` - Get file info
- `file.Walk` - Recursive directory walk
- `file.Write` - Write file (restricted to working dir)

### 9. Filepath Functions (`filepath.`)
- `filepath.Base` / `filepath.Dir` / `filepath.Ext`
- `filepath.Join` / `filepath.Split`
- `filepath.Clean` / `filepath.Abs`
- `filepath.Rel` / `filepath.Match`

### 10. GCP Functions (`gcp.`)
- `gcp.Meta` - GCE instance metadata

### 11. Math Functions (`math.`)
- `add` / `sub` / `mul` / `div` - Basic arithmetic
- `math.Abs` / `math.Ceil` / `math.Floor` / `math.Round`
- `math.Max` / `math.Min`
- `math.Pow` / `math.Sqrt` / `math.Log`
- `math.Rem` - Remainder/modulo
- `math.Seq` / `seq` - Generate number sequences

### 12. Net Functions (`net.`)
- `net.LookupIP` - DNS lookup
- `net.LookupCNAME` / `net.LookupSRV` / `net.LookupTXT`
- `net.ParseIP` / `net.ParseIPPrefix`

### 13. Path Functions (`path.`)
- `path.Base` / `path.Dir` / `path.Ext`
- `path.Join` / `path.Split` / `path.Clean`
- `path.Match` / `path.IsAbs`

### 14. Random Functions (`random.`)
- `random.ASCII` - Random ASCII string
- `random.Alpha` - Random alphabetic string
- `random.AlphaNum` - Random alphanumeric string
- `random.String` - Random string from character set
- `random.Number` - Random integer
- `random.Float` - Random float
- `random.Item` - Random item from array

### 15. Regexp Functions (`regexp.`)
- `regexp.Match` - Test if pattern matches
- `regexp.Find` / `regexp.FindAll` - Find matches
- `regexp.Replace` / `regexp.ReplaceLiteral` - Replace matches
- `regexp.Split` - Split string by pattern
- `regexp.QuoteMeta` - Escape special characters

### 16. Semver Functions (`semver.`)
- `semver.Semver` - Parse semantic version
- `semver.CheckConstraint` - Check version constraints

### 17. Sockaddr Functions (`sockaddr.`)
- Network address introspection (from HashiCorp's go-sockaddr)
- `sockaddr.GetAllInterfaces` / `sockaddr.GetInterfaceIP`
- `sockaddr.GetPrivateIP` / `sockaddr.GetPublicIP`

### 18. String Functions (`strings.`)
- `strings.ToUpper` / `strings.ToLower` / `strings.Title`
- `strings.TrimSpace` / `strings.Trim` / `strings.TrimPrefix` / `strings.TrimSuffix`
- `strings.Contains` / `strings.HasPrefix` / `strings.HasSuffix`
- `strings.Split` / `strings.SplitN`
- `strings.Join`
- `strings.Replace` / `strings.ReplaceAll`
- `strings.Repeat`
- `strings.Indent` - Add indentation
- `strings.Abbrev` - Abbreviate with ellipsis
- `strings.WordWrap` - Wrap text
- `strings.RuneCount` - Count characters
- `strings.Quote` / `strings.ShellQuote`
- `strings.Slug` - URL-friendly slugs
- `strings.SkipLines` - Skip lines from start

### 19. Template Functions (`tmpl.`)
- `tmpl.Exec` - Execute named template and return string
- `tpl` - Render string as template
- `tmpl.Path` - Get current template path

### 20. Test Functions (`test.`)
- `test.Assert` / `assert` - Assert condition is true
- `test.Fail` / `fail` - Fail template rendering
- `test.Required` / `required` - Require non-empty value

### 21. Time Functions (`time.`)
- `time.Now` - Current time
- `time.Parse` / `time.ParseLocal` / `time.ParseInLocation`
- `time.Format` / `time.FormatLocal`
- `time.Unix` / `time.ZoneName` / `time.ZoneOffset`
- `time.Since` / `time.Until`

### 22. UUID Functions (`uuid.`)
- `uuid.V1` - Generate UUID v1
- `uuid.V4` - Generate UUID v4
- `uuid.Nil` - Nil UUID
- `uuid.IsValid` - Validate UUID
- `uuid.Parse` - Parse UUID string

---

## Use Cases & Patterns

### 1. Configuration File Generation

**Generate nginx.conf from YAML config:**
```yaml
# config.yaml
server:
  port: 8080
  workers: 4
upstream:
  servers:
    - backend1.example.com
    - backend2.example.com
```

```nginx
# nginx.conf.tmpl
worker_processes {{ (ds "config").server.workers }};

http {
    upstream backend {
        {{ range (ds "config").upstream.servers -}}
        server {{ . }};
        {{ end -}}
    }
    
    server {
        listen {{ (ds "config").server.port }};
        location / {
            proxy_pass http://backend;
        }
    }
}
```

```bash
gomplate -d config=./config.yaml -f nginx.conf.tmpl -o nginx.conf
```

### 2. Kubernetes Manifest Templating

**Generate deployment with environment-specific values:**
```yaml
# deployment.yaml.tmpl
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Env.APP_NAME }}
  namespace: {{ .Env.NAMESPACE | default "default" }}
spec:
  replicas: {{ .Env.REPLICAS | default "1" | conv.ToInt }}
  template:
    spec:
      containers:
      - name: {{ .Env.APP_NAME }}
        image: {{ .Env.IMAGE }}:{{ .Env.TAG }}
        env:
        {{- range $key, $value := (ds "secrets") }}
        - name: {{ $key }}
          value: {{ $value | quote }}
        {{- end }}
```

```bash
export APP_NAME=myapp NAMESPACE=prod REPLICAS=3 IMAGE=myrepo/myapp TAG=v1.2.3
gomplate -d secrets=vault:///secret/myapp/prod -f deployment.yaml.tmpl
```

### 3. Init Container for Configuration

**Dockerfile:**
```dockerfile
FROM alpine
COPY --from=hairyhenderson/gomplate:stable /gomplate /bin/gomplate
COPY templates/ /templates/
ENTRYPOINT ["gomplate", "--input-dir=/templates", "--output-dir=/config"]
```

**Kubernetes init container:**
```yaml
initContainers:
- name: config-init
  image: myorg/gomplate-config
  volumeMounts:
  - name: config-volume
    mountPath: /config
  - name: params-configmap
    mountPath: /params
  env:
  - name: VAULT_ADDR
    value: "https://vault.example.com"
```

### 4. Secret Injection

**Inject Vault secrets into application config:**
```yaml
# app.conf.tmpl
database:
  host: {{ (ds "vault" "db/creds").host }}
  username: {{ (ds "vault" "db/creds").username }}
  password: {{ (ds "vault" "db/creds").password }}
  
api_keys:
  stripe: {{ (ds "vault" "api/stripe").key }}
  sendgrid: {{ (ds "vault" "api/sendgrid").key }}
```

### 5. Multi-Environment Configuration

**Merge environment-specific overrides with defaults:**
```bash
gomplate -d "config=merge:./envs/${ENV}.yaml|./defaults.yaml" \
         -f app.conf.tmpl -o app.conf
```

### 6. Batch Processing

**Process all templates in a directory:**
```bash
gomplate --input-dir=./templates \
         --output-dir=./output \
         --datasource config=./config.yaml \
         --exclude "*.bak"
```

### 7. Dynamic Secrets with AWS

```bash
# AWS Systems Manager Parameter Store
gomplate -d params=aws+smp:///prod/myapp/ \
         -i 'DB_PASS={{ (ds "params" "db_password").Value }}'

# AWS Secrets Manager
gomplate -d secrets=aws+sm:///prod/myapp/db \
         -i 'DB_PASS={{ ds "secrets" }}'
```

### 8. CI/CD Pipeline Integration

**GitLab CI example:**
```yaml
generate-config:
  image: hairyhenderson/gomplate:stable
  script:
    - gomplate -d config=./config.yaml -f deployment.tmpl -o deployment.yaml
  artifacts:
    paths:
      - deployment.yaml
```

---

## Integration with DevOps Tools

### With Helm (Post-Renderer)

Use gomplate as a Helm post-renderer for additional templating capabilities:

```bash
# Set different delimiters to avoid conflicts
export GOMPLATE_LEFT_DELIM="[["
export GOMPLATE_RIGHT_DELIM="]]"

# Create post-renderer script
cat > gomplate-renderer.sh << 'EOF'
#!/bin/bash
cat | gomplate
EOF
chmod +x gomplate-renderer.sh

# Use with Helm
helm install myrelease mychart --post-renderer ./gomplate-renderer.sh
```

### With Docker Compose

```yaml
# docker-compose.yml.tmpl
version: '3'
services:
  app:
    image: myapp:{{ .Env.VERSION }}
    environment:
      - DATABASE_URL={{ (ds "secrets").database_url }}
    deploy:
      replicas: {{ .Env.REPLICAS | default "1" }}
```

### With Terraform

```hcl
# Use gomplate to generate tfvars
data "external" "config" {
  program = ["gomplate", "-d", "config=./config.yaml", "-i", "..."]
}
```

### With Ansible

```yaml
# Generate Ansible inventory dynamically
- name: Generate inventory
  command: gomplate -d hosts=consul:///hosts -f inventory.tmpl -o inventory
```

---

## Configuration Options

### Command-Line Flags

| Flag | Description |
|------|-------------|
| `-f`, `--file` | Input template file (use `-` for stdin) |
| `-i`, `--in` | Inline template string |
| `-o`, `--out` | Output file (default: stdout) |
| `-d`, `--datasource` | Define datasource (alias=URL) |
| `-c`, `--context` | Pre-load datasource into context |
| `-H`, `--datasource-header` | HTTP headers for datasources |
| `-t`, `--template` | Additional template files |
| `--input-dir` | Process all templates in directory |
| `--output-dir` | Output directory for batch processing |
| `--output-map` | Template for output filenames |
| `--exclude` | Glob patterns to exclude |
| `--exclude-processing` | Copy files without processing |
| `--config` | Config file path (default: .gomplate.yaml) |
| `--plugin` | Add custom plugin function |
| `--left-delim` | Left template delimiter (default: `{{`) |
| `--right-delim` | Right template delimiter (default: `}}`) |
| `--exec-pipe` | Pipe output to command |
| `--verbose` | Enable verbose logging |
| `--experimental` | Enable experimental features |

### Configuration File (.gomplate.yaml)

```yaml
# .gomplate.yaml
inputDir: ./templates
outputDir: ./output

datasources:
  config:
    url: ./config.yaml
  vault:
    url: vault:///secret/myapp

context:
  env: env:ENV

plugins:
  myfunction: /usr/local/bin/my-plugin

templates:
  helpers: ./helpers/

leftDelim: "[["
rightDelim: "]]"

experimental: true
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `GOMPLATE_CONFIG` | Config file path |
| `GOMPLATE_LEFT_DELIM` | Left delimiter |
| `GOMPLATE_RIGHT_DELIM` | Right delimiter |
| `GOMPLATE_SUPPRESS_EMPTY` | Don't write empty files |
| `GOMPLATE_TYPE_PARAM` | Query param name for MIME type override |
| `GOMPLATE_LOG_FORMAT` | Log format (`json` or `console`) |

### Datasource-Specific Variables

**Consul:**
- `CONSUL_HTTP_ADDR`, `CONSUL_HTTP_TOKEN`, `CONSUL_HTTP_SSL`

**Vault:**
- `VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_ROLE_ID`, `VAULT_SECRET_ID`
- `VAULT_AUTH_*` for various auth methods

**AWS:**
- `AWS_REGION`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_ENDPOINT` for S3-compatible storage

---

## Best Practices

### 1. Use Configuration Files

Keep datasource definitions in `.gomplate.yaml` rather than long command lines:

```yaml
# .gomplate.yaml
datasources:
  defaults: ./defaults.yaml
  overrides: ./envs/${ENV}.yaml
  secrets: vault:///secret/myapp
```

### 2. Validate Required Values

Use `required` to fail early on missing data:

```go
{{ $db_host := .Env.DB_HOST | required "DB_HOST must be set" }}
```

### 3. Provide Sensible Defaults

Use `default` for optional values:

```go
replicas: {{ .Env.REPLICAS | default "1" }}
log_level: {{ getenv "LOG_LEVEL" "info" }}
```

### 4. Use Nested Templates for Reusability

```go
# Define reusable template
{{ define "connection_string" -}}
postgresql://{{ .user }}:{{ .pass }}@{{ .host }}:{{ .port }}/{{ .db }}
{{- end }}

# Use it
database_url: {{ template "connection_string" (ds "db_config") }}
```

### 5. Handle Missing Datasources Gracefully

```go
{{ if datasourceReachable "optional_config" }}
  {{ (ds "optional_config").setting }}
{{ else }}
  default_value
{{ end }}
```

### 6. Use Type Assertions

Convert types explicitly:

```go
{{ $count := .Env.COUNT | conv.ToInt }}
{{ if gt $count 10 }}...{{ end }}
```

### 7. Organize Complex Templates

- Split into multiple files with `--template`
- Use `{{ define }}` and `{{ template }}` for components
- Keep templates focused and modular

---

## Comparison with Alternatives

| Feature | gomplate | envsubst | Helm | Jinja2 | Consul-Template |
|---------|----------|----------|------|--------|-----------------|
| **Binary size** | ~15MB | tiny | ~45MB | Requires Python | ~20MB |
| **Dependencies** | None | None | Kubernetes | Python runtime | None |
| **Learning curve** | Medium | Low | High | Medium | Medium |
| **Datasources** | 12+ types | Env only | Values files | Files | Consul, Vault |
| **Functions** | 200+ | 0 | ~100 (Sprig) | Extensive | ~50 |
| **Conditionals** | Yes | No | Yes | Yes | Yes |
| **Loops** | Yes | No | Yes | Yes | Yes |
| **Vault support** | Native | No | Via secrets | Manual | Native |
| **AWS support** | Native | No | No | Manual | No |
| **Kubernetes focus** | General | General | Yes | General | General |
| **Watch mode** | No | No | No | No | Yes |

### When to Use Gomplate

✅ **Use gomplate when:**
- You need a single binary with no runtime dependencies
- You require multiple datasource types (Vault, Consul, AWS, etc.)
- You want extensive function library beyond basic substitution
- You're in containerized/Kubernetes environments
- You need conditional logic and loops in templates

❌ **Consider alternatives when:**
- Simple `$VAR` substitution is sufficient (use envsubst)
- You need Kubernetes package management (use Helm)
- You need live configuration reloading (use Consul-Template)
- Your team is Python-native and needs complex logic (use Jinja2)

---

## Version History & Breaking Changes

### Version 4.0.0 (Current Major)

**Key Changes:**
- Removed BoltDB datasource support
- Removed "slim" binary variants
- Changed subpath resolution for datasources (now relative URL resolution)
- AWS SSM Parameter Store (`aws+smp`) returns data directly instead of full Parameter object
- Consul directory listings return string arrays instead of JSON objects
- Removed deprecated Vault "app-id" authentication
- Empty whitespace-only output is no longer written by default

**Migration Notes:**
- Update `aws+smp` usage: `{{ (ds "params").Value }}` → `{{ ds "params" }}`
- Update Consul directory iteration logic
- Check subpath handling in datasource definitions

### Version 3.x

- Introduced experimental `Renderer` API for library usage
- Added AWS IMDSv2 support
- Added `break` and `continue` for loops (Go 1.18)
- Plugin stdin piping support

### Version 2.x → 3.x

- Many function namespaces reorganized
- Datasource URL handling standardized

---

## Resources

- **Documentation:** https://docs.gomplate.ca
- **GitHub Repository:** https://github.com/hairyhenderson/gomplate
- **Docker Hub:** https://hub.docker.com/r/hairyhenderson/gomplate
- **Slack:** #gomplate channel on Gophers Slack
- **Issue Tracker:** https://github.com/hairyhenderson/gomplate/issues

---

## Quick Reference

### Essential Commands

```bash
# Basic usage
gomplate -i 'Hello {{ .Env.USER }}'

# File input/output
gomplate -f template.tmpl -o output.txt

# With datasource
gomplate -d config=./config.yaml -f template.tmpl

# Batch processing
gomplate --input-dir=./templates --output-dir=./output -d config=./config.yaml

# Use config file
gomplate --config=.gomplate.yaml
```

### Essential Functions

```go
# Get env with default
{{ getenv "VAR" "default" }}

# Datasource access
{{ (datasource "name").key }}
{{ ds "name" "subpath" }}

# Type conversion
{{ .value | conv.ToInt }}

# Conditionals
{{ if eq .Env.ENV "prod" }}...{{ end }}

# Loops
{{ range (ds "items") }}{{ . }}{{ end }}

# String operations
{{ "hello" | strings.ToUpper }}

# Required values
{{ .Env.REQUIRED | required "Missing REQUIRED" }}
```
