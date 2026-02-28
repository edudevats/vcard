import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../../config/app_config.dart';

/// Cliente HTTP centralizado para la API REST de ATScard.
class ApiClient {
  static String? _token;

  static void setToken(String? token) => _token = token;
  static String? get token => _token;
  static bool get isAuthenticated => _token != null;

  static Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  // ── GET ────────────────────────────────────────────────────────────────
  static Future<ApiResponse> get(String path,
      {Map<String, String>? queryParams}) async {
    try {
      var uri = Uri.parse('${AppConfig.apiUrl}$path');
      if (queryParams != null) {
        uri = uri.replace(queryParameters: queryParams);
      }
      final res = await http
          .get(uri, headers: _headers)
          .timeout(AppConfig.receiveTimeout);
      return _parse(res);
    } on SocketException {
      return ApiResponse.error('Sin conexión a internet');
    } on TimeoutException {
      return ApiResponse.error('Tiempo de espera agotado');
    } catch (e) {
      return ApiResponse.error('Error inesperado: $e');
    }
  }

  // ── POST ───────────────────────────────────────────────────────────────
  static Future<ApiResponse> post(String path, {Map<String, dynamic>? body}) async {
    try {
      final res = await http
          .post(
            Uri.parse('${AppConfig.apiUrl}$path'),
            headers: _headers,
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(AppConfig.receiveTimeout);
      return _parse(res);
    } on SocketException {
      return ApiResponse.error('Sin conexión a internet');
    } on TimeoutException {
      return ApiResponse.error('Tiempo de espera agotado');
    } catch (e) {
      return ApiResponse.error('Error inesperado: $e');
    }
  }

  // ── PUT ────────────────────────────────────────────────────────────────
  static Future<ApiResponse> put(String path, {Map<String, dynamic>? body}) async {
    try {
      final res = await http
          .put(
            Uri.parse('${AppConfig.apiUrl}$path'),
            headers: _headers,
            body: body != null ? jsonEncode(body) : null,
          )
          .timeout(AppConfig.receiveTimeout);
      return _parse(res);
    } on SocketException {
      return ApiResponse.error('Sin conexión a internet');
    } on TimeoutException {
      return ApiResponse.error('Tiempo de espera agotado');
    } catch (e) {
      return ApiResponse.error('Error inesperado: $e');
    }
  }

  // ── DELETE ─────────────────────────────────────────────────────────────
  static Future<ApiResponse> delete(String path) async {
    try {
      final res = await http
          .delete(Uri.parse('${AppConfig.apiUrl}$path'), headers: _headers)
          .timeout(AppConfig.receiveTimeout);
      return _parse(res);
    } on SocketException {
      return ApiResponse.error('Sin conexión a internet');
    } on TimeoutException {
      return ApiResponse.error('Tiempo de espera agotado');
    } catch (e) {
      return ApiResponse.error('Error inesperado: $e');
    }
  }

  // ── Parser ─────────────────────────────────────────────────────────────
  static ApiResponse _parse(http.Response res) {
    try {
      final body = jsonDecode(utf8.decode(res.bodyBytes));
      if (res.statusCode >= 200 && res.statusCode < 300) {
        return ApiResponse.success(body, statusCode: res.statusCode);
      }
      final message = body is Map ? (body['error'] ?? body['message'] ?? 'Error') : 'Error';
      return ApiResponse.error(message.toString(), statusCode: res.statusCode);
    } catch (e) {
      return ApiResponse.error('Error al procesar la respuesta');
    }
  }

  /// Construye URL completa de imagen (para avatars y fotos del servidor)
  static String imageUrl(String? path) {
    if (path == null || path.isEmpty) return '';
    if (path.startsWith('http')) return path;
    return '${AppConfig.baseUrl}$path';
  }
}

/// Resultado de una llamada a la API.
class ApiResponse {
  final bool success;
  final dynamic data;
  final String? error;
  final int statusCode;

  const ApiResponse._({
    required this.success,
    this.data,
    this.error,
    this.statusCode = 200,
  });

  factory ApiResponse.success(dynamic data, {int statusCode = 200}) =>
      ApiResponse._(success: true, data: data, statusCode: statusCode);

  factory ApiResponse.error(String message, {int statusCode = 0}) =>
      ApiResponse._(success: false, error: message, statusCode: statusCode);

  bool get isUnauthorized => statusCode == 401;
  bool get isForbidden => statusCode == 403;
}
