/// Modelos de datos para la app ATScard.
library;

// ── User ──────────────────────────────────────────────────────────────────

class UserModel {
  final int id;
  final String email;
  final String role;
  final int maxCards;
  final int cardsCount;
  final bool canCreateCard;
  final bool hasTicketSystem;

  const UserModel({
    required this.id,
    required this.email,
    required this.role,
    required this.maxCards,
    required this.cardsCount,
    required this.canCreateCard,
    required this.hasTicketSystem,
  });

  factory UserModel.fromJson(Map<String, dynamic> j) => UserModel(
        id: j['id'] ?? 0,
        email: j['email'] ?? '',
        role: j['role'] ?? 'user',
        maxCards: j['max_cards'] ?? 1,
        cardsCount: j['cards_count'] ?? 0,
        canCreateCard: j['can_create_card'] ?? false,
        hasTicketSystem: j['has_ticket_system'] ?? false,
      );

  bool get isAdmin => role == 'admin';
}

// ── Card ──────────────────────────────────────────────────────────────────

class CardModel {
  final int id;
  final String slug;
  final String title;
  final String name;
  final String? jobTitle;
  final String? company;
  final String? phone;
  final String? emailPublic;
  final String? website;
  final String? location;
  final String? bio;
  final bool isPublic;
  final String? avatarUrl;
  final String publicUrl;
  final String? createdAt;
  final String? updatedAt;
  // Details (only when fetched individually)
  final String? instagram;
  final String? facebook;
  final String? linkedin;
  final String? twitter;
  final String? youtube;
  final String? tiktok;
  final String? telegram;
  final String? whatsapp;
  final String? whatsappCountry;
  final String? github;
  final CardThemeModel? theme;
  final int servicesCount;
  final int galleryCount;

  const CardModel({
    required this.id,
    required this.slug,
    required this.title,
    required this.name,
    this.jobTitle,
    this.company,
    this.phone,
    this.emailPublic,
    this.website,
    this.location,
    this.bio,
    required this.isPublic,
    this.avatarUrl,
    required this.publicUrl,
    this.createdAt,
    this.updatedAt,
    this.instagram,
    this.facebook,
    this.linkedin,
    this.twitter,
    this.youtube,
    this.tiktok,
    this.telegram,
    this.whatsapp,
    this.whatsappCountry,
    this.github,
    this.theme,
    this.servicesCount = 0,
    this.galleryCount = 0,
  });

  factory CardModel.fromJson(Map<String, dynamic> j) => CardModel(
        id: j['id'] ?? 0,
        slug: j['slug'] ?? '',
        title: j['title'] ?? j['name'] ?? '',
        name: j['name'] ?? '',
        jobTitle: j['job_title'],
        company: j['company'],
        phone: j['phone'],
        emailPublic: j['email_public'],
        website: j['website'],
        location: j['location'],
        bio: j['bio'],
        isPublic: j['is_public'] ?? false,
        avatarUrl: j['avatar_url'],
        publicUrl: j['public_url'] ?? '',
        createdAt: j['created_at'],
        updatedAt: j['updated_at'],
        instagram: j['instagram'],
        facebook: j['facebook'],
        linkedin: j['linkedin'],
        twitter: j['twitter'],
        youtube: j['youtube'],
        tiktok: j['tiktok'],
        telegram: j['telegram'],
        whatsapp: j['whatsapp'],
        whatsappCountry: j['whatsapp_country'],
        github: j['github'],
        theme: j['theme'] != null ? CardThemeModel.fromJson(j['theme']) : null,
        servicesCount: j['services_count'] ?? 0,
        galleryCount: j['gallery_count'] ?? 0,
      );
}

class CardThemeModel {
  final String? name;
  final String primaryColor;
  final String secondaryColor;
  final String accentColor;
  final String fontFamily;
  final String layout;
  final String avatarShape;

  const CardThemeModel({
    this.name,
    required this.primaryColor,
    required this.secondaryColor,
    required this.accentColor,
    required this.fontFamily,
    required this.layout,
    required this.avatarShape,
  });

  factory CardThemeModel.fromJson(Map<String, dynamic> j) => CardThemeModel(
        name: j['name'],
        primaryColor: j['primary_color'] ?? '#6366f1',
        secondaryColor: j['secondary_color'] ?? '#8b5cf6',
        accentColor: j['accent_color'] ?? '#ec4899',
        fontFamily: j['font_family'] ?? 'Inter',
        layout: j['layout'] ?? 'modern',
        avatarShape: j['avatar_shape'] ?? 'circle',
      );
}

// ── Service ───────────────────────────────────────────────────────────────

class ServiceModel {
  final int id;
  final String title;
  final String? description;
  final dynamic priceFrom;
  final String? icon;
  final String? category;
  final int? duration;
  final bool isFeatured;
  final bool isVisible;
  final bool acceptsAppointments;
  final int orderIndex;
  final String? imagePath;

  const ServiceModel({
    required this.id,
    required this.title,
    this.description,
    this.priceFrom,
    this.icon,
    this.category,
    this.duration,
    required this.isFeatured,
    required this.isVisible,
    required this.acceptsAppointments,
    required this.orderIndex,
    this.imagePath,
  });

  factory ServiceModel.fromJson(Map<String, dynamic> j) => ServiceModel(
        id: j['id'] ?? 0,
        title: j['title'] ?? '',
        description: j['description'],
        priceFrom: j['price_from'],
        icon: j['icon'],
        category: j['category'],
        duration: j['duration'],
        isFeatured: j['is_featured'] ?? false,
        isVisible: j['is_visible'] ?? true,
        acceptsAppointments: j['accepts_appointments'] ?? false,
        orderIndex: j['order_index'] ?? 0,
        imagePath: j['image_path'],
      );
}

// ── Appointment ───────────────────────────────────────────────────────────

class AppointmentModel {
  final int id;
  final String customerName;
  final String customerPhone;
  final String? customerPhoneCountry;
  final String? customerAddress;
  final String? appointmentDate;
  final String? appointmentTime;
  final String status;
  final String? notes;
  final String? cancellationReason;
  final int serviceId;
  final String? serviceName;
  final int cardId;
  final String? createdAt;
  final String? confirmedAt;

  const AppointmentModel({
    required this.id,
    required this.customerName,
    required this.customerPhone,
    this.customerPhoneCountry,
    this.customerAddress,
    this.appointmentDate,
    this.appointmentTime,
    required this.status,
    this.notes,
    this.cancellationReason,
    required this.serviceId,
    this.serviceName,
    required this.cardId,
    this.createdAt,
    this.confirmedAt,
  });

  factory AppointmentModel.fromJson(Map<String, dynamic> j) => AppointmentModel(
        id: j['id'] ?? 0,
        customerName: j['customer_name'] ?? '',
        customerPhone: j['customer_phone'] ?? '',
        customerPhoneCountry: j['customer_phone_country'],
        customerAddress: j['customer_address'],
        appointmentDate: j['appointment_date'],
        appointmentTime: j['appointment_time'],
        status: j['status'] ?? 'pending',
        notes: j['notes'],
        cancellationReason: j['cancellation_reason'],
        serviceId: j['service_id'] ?? 0,
        serviceName: j['service_name'],
        cardId: j['card_id'] ?? 0,
        createdAt: j['created_at'],
        confirmedAt: j['confirmed_at'],
      );

  String get fullPhone {
    if (customerPhoneCountry != null && customerPhoneCountry!.isNotEmpty) {
      return '$customerPhoneCountry$customerPhone';
    }
    return customerPhone;
  }
}

// ── Ticket ────────────────────────────────────────────────────────────────

class TicketModel {
  final int id;
  final String ticketNumber;
  final String patientName;
  final String? patientPhone;
  final String status;
  final int? ticketTypeId;
  final String? ticketTypeName;
  final String? ticketTypeColor;
  final bool isPriority;
  final String? createdAt;
  final String? calledAt;
  final String? completedAt;
  final String? notes;

  const TicketModel({
    required this.id,
    required this.ticketNumber,
    required this.patientName,
    this.patientPhone,
    required this.status,
    this.ticketTypeId,
    this.ticketTypeName,
    this.ticketTypeColor,
    required this.isPriority,
    this.createdAt,
    this.calledAt,
    this.completedAt,
    this.notes,
  });

  factory TicketModel.fromJson(Map<String, dynamic> j) => TicketModel(
        id: j['id'] ?? 0,
        ticketNumber: j['ticket_number'] ?? '',
        patientName: j['patient_name'] ?? '',
        patientPhone: j['patient_phone'],
        status: j['status'] ?? 'waiting',
        ticketTypeId: j['ticket_type_id'],
        ticketTypeName: j['ticket_type_name'],
        ticketTypeColor: j['ticket_type_color'],
        isPriority: j['is_priority'] ?? false,
        createdAt: j['created_at'],
        calledAt: j['called_at'],
        completedAt: j['completed_at'],
        notes: j['notes'],
      );
}

// ── Dashboard ─────────────────────────────────────────────────────────────

class DashboardData {
  final int cardsCount;
  final int maxCards;
  final int viewsToday;
  final int pendingAppointments;
  final Map<String, dynamic>? ticketStats;
  final List<AppointmentModel> recentAppointments;
  final List<CardModel> cards;

  const DashboardData({
    required this.cardsCount,
    required this.maxCards,
    required this.viewsToday,
    required this.pendingAppointments,
    this.ticketStats,
    required this.recentAppointments,
    required this.cards,
  });

  factory DashboardData.fromJson(Map<String, dynamic> j) => DashboardData(
        cardsCount: j['cards_count'] ?? 0,
        maxCards: j['max_cards'] ?? 1,
        viewsToday: j['views_today'] ?? 0,
        pendingAppointments: j['pending_appointments'] ?? 0,
        ticketStats: j['ticket_stats'],
        recentAppointments: (j['recent_appointments'] as List? ?? [])
            .map((a) => AppointmentModel.fromJson(a))
            .toList(),
        cards: (j['cards'] as List? ?? [])
            .map((c) => CardModel.fromJson(c))
            .toList(),
      );
}
