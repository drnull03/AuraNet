{{/*
Expand the name of the chart.
*/}}
{{- define "auranet-encryption.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "auranet-encryption.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ include "auranet-encryption.name" . }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: auranet-encryption
security.auranet/pqc-enabled: "true"
{{- end }}

{{/*
KEM curves as YAML list — pulled from values.pqc.kemCurves
*/}}
{{- define "auranet-encryption.kemCurves" -}}
{{- range .Values.pqc.kemCurves }}
- {{ . }}
{{- end }}
{{- end }}

{{/*
Upstream (outbound) TLS context patch value
*/}}
{{- define "auranet-encryption.upstreamTlsContext" -}}
name: envoy.transport_sockets.tls
typed_config:
  "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
  common_tls_context:
    tls_params:
      tls_minimum_protocol_version: {{ .Values.pqc.tls.minVersion }}
      tls_maximum_protocol_version: {{ .Values.pqc.tls.maxVersion }}
      ecdh_curves:
        {{- include "auranet-encryption.kemCurves" . | nindent 8 }}
{{- end }}

{{/*
Downstream (inbound) TLS context patch value
*/}}
{{- define "auranet-encryption.downstreamTlsContext" -}}
name: envoy.transport_sockets.tls
typed_config:
  "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.DownstreamTlsContext
  common_tls_context:
    tls_params:
      tls_minimum_protocol_version: {{ .Values.pqc.tls.minVersion }}
      tls_maximum_protocol_version: {{ .Values.pqc.tls.maxVersion }}
      ecdh_curves:
        {{- include "auranet-encryption.kemCurves" . | nindent 8 }}
{{- end }}
