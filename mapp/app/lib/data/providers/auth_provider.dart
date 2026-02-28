import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/network/api_client.dart';
import '../models/models.dart';

enum AuthStatus { unknown, authenticated, unauthenticated }

class AuthProvider extends ChangeNotifier {
  static const _storage = FlutterSecureStorage();
  static const _tokenKey = 'atscard_token';

  AuthStatus _status = AuthStatus.unknown;
  UserModel? _user;
  String? _error;
  bool _loading = false;

  AuthStatus get status => _status;
  UserModel? get user => _user;
  String? get error => _error;
  bool get loading => _loading;
  bool get isAuthenticated => _status == AuthStatus.authenticated;

  // ── Init ────────────────────────────────────────────────────────────────

  Future<void> init() async {
    final token = await _storage.read(key: _tokenKey);
    if (token != null) {
      ApiClient.setToken(token);
      await _fetchMe();
    } else {
      _status = AuthStatus.unauthenticated;
      notifyListeners();
    }
  }

  // ── Login ────────────────────────────────────────────────────────────────

  Future<bool> login(String email, String password) async {
    _loading = true;
    _error = null;
    notifyListeners();

    final res = await ApiClient.post('/auth/login', body: {
      'email': email.trim().toLowerCase(),
      'password': password,
    });

    _loading = false;

    if (res.success) {
      final token = res.data['token'] as String;
      await _storage.write(key: _tokenKey, value: token);
      ApiClient.setToken(token);
      await _fetchMe();
      return true;
    } else {
      _error = res.error;
      notifyListeners();
      return false;
    }
  }

  // ── Logout ────────────────────────────────────────────────────────────────

  Future<void> logout() async {
    await ApiClient.post('/auth/logout');
    ApiClient.setToken(null);
    await _storage.delete(key: _tokenKey);
    _user = null;
    _status = AuthStatus.unauthenticated;
    notifyListeners();
  }

  // ── Fetch user profile ────────────────────────────────────────────────────

  Future<void> _fetchMe() async {
    final res = await ApiClient.get('/auth/me');
    if (res.success) {
      _user = UserModel.fromJson(res.data);
      _status = AuthStatus.authenticated;
    } else if (res.isUnauthorized) {
      await _storage.delete(key: _tokenKey);
      ApiClient.setToken(null);
      _status = AuthStatus.unauthenticated;
    } else {
      // Network error → keep token but report issue
      _status = AuthStatus.unauthenticated;
      _error = res.error;
    }
    notifyListeners();
  }

  Future<void> refreshUser() => _fetchMe();

  void clearError() {
    _error = null;
    notifyListeners();
  }
}
