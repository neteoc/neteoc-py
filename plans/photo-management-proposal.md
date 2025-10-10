# Complete Photo Management System Proposal

**Author**: Jake Harrison
**Date**: 2025-08-04
**Status**: Future Enhancement
**Priority**: Medium

## Overview

Expand profile photo system to support user uploads with comprehensive image processing pipeline for professional disaster response identification. This proposal was extracted from the user profile enhancements scope to focus on rapid MVP delivery while maintaining proper architecture for future photo management capabilities.

## GitHub Issue Content

**Title**: Implement Complete Profile Photo Management with Upload Pipeline

**Labels**: `enhancement`, `photos`, `media-processing`

**Description:**
Expand profile photo system to support user uploads with comprehensive image processing pipeline for professional disaster response identification.

**Requirements:**
- Secure photo upload with file type and size validation
- Image processing pipeline (resize, crop, EXIF removal)
- Multiple thumbnail sizes for responsive display
- Cloud storage integration (S3/CloudFlare R2)
- Admin moderation capabilities for uploaded photos
- Batch photo processing for organizational imports
- CDN integration for optimal loading performance

**Technical Architecture:**
```python
# user_profile/models.py (extensions)
class UserProfile(models.Model):
    # Existing fields...
    profile_photo = ImageField(
        upload_to='profile_photos/%Y/%m/',
        null=True,
        blank=True,
        validators=[validate_image_file]
    )
    photo_thumbnails = JSONField(default=dict, blank=True, help_text="Store thumbnail URLs")
    photo_uploaded_at = DateTimeField(null=True, blank=True)
    photo_approved = BooleanField(default=True, help_text="Admin moderation flag")
    photo_processing_status = CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending Processing'),
            ('PROCESSING', 'Processing'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Processing Failed'),
        ],
        default='COMPLETED'
    )

    # Enhanced Gravatar fields (already in MVP)
    use_gravatar = BooleanField(default=True)
    gravatar_email = EmailField(blank=True)

class PhotoProcessingJob(models.Model):
    """Track photo processing operations"""
    user_profile = ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='photo_jobs')
    original_filename = CharField(max_length=255)
    original_size_bytes = PositiveIntegerField()
    processing_status = CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('PROCESSING', 'Processing'),
            ('COMPLETED', 'Completed'),
            ('FAILED', 'Failed'),
        ],
        default='PENDING'
    )
    created_at = DateTimeField(auto_now_add=True)
    started_at = DateTimeField(null=True, blank=True)
    completed_at = DateTimeField(null=True, blank=True)
    error_message = TextField(blank=True)

    # Processing details
    thumbnails_created = JSONField(default=dict, blank=True)
    final_file_size = PositiveIntegerField(null=True, blank=True)
    cdn_urls = JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['processing_status', 'created_at']),
            models.Index(fields=['user_profile', 'processing_status']),
        ]

class PhotoModerationLog(models.Model):
    """Track admin photo moderation actions"""
    user_profile = ForeignKey(UserProfile, on_delete=models.CASCADE)
    moderator = ForeignKey(User, on_delete=models.PROTECT)
    action = CharField(
        max_length=20,
        choices=[
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected'),
            ('FLAGGED', 'Flagged for Review'),
        ]
    )
    reason = TextField(blank=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
```

**Image Processing Pipeline:**
```python
# user_profile/photo_processing.py
from PIL import Image, ImageOps
from pillow_heif import register_heif_opener
import hashlib
import boto3
from django.conf import settings

# Register HEIF support for iPhone photos
register_heif_opener()

class PhotoProcessor:
    THUMBNAIL_SIZES = {
        'small': (75, 75),
        'medium': (150, 150),
        'large': (300, 300),
        'xlarge': (500, 500),
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_FORMATS = ['JPEG', 'PNG', 'WEBP', 'HEIF']
    QUALITY_SETTINGS = {
        'JPEG': 85,
        'WEBP': 80,
        'PNG': None,  # PNG is lossless
    }

    def __init__(self, storage_backend='s3'):
        self.storage_backend = storage_backend
        if storage_backend == 's3':
            self.s3_client = boto3.client('s3')

    def validate_upload(self, uploaded_file):
        """Validate uploaded file before processing"""
        # Check file size
        if uploaded_file.size > self.MAX_FILE_SIZE:
            raise ValidationError(f'File size {uploaded_file.size} exceeds maximum {self.MAX_FILE_SIZE} bytes')

        # Check file type
        try:
            with Image.open(uploaded_file) as img:
                if img.format not in self.ALLOWED_FORMATS:
                    raise ValidationError(f'Unsupported format: {img.format}')

                # Check image dimensions
                if img.width > 5000 or img.height > 5000:
                    raise ValidationError('Image dimensions too large (max 5000x5000)')

                # Check for potential malicious content
                img.verify()

        except Exception as e:
            raise ValidationError(f'Invalid image file: {str(e)}')

    def process_profile_photo(self, user_profile, uploaded_file):
        """Complete photo processing pipeline"""
        job = PhotoProcessingJob.objects.create(
            user_profile=user_profile,
            original_filename=uploaded_file.name,
            original_size_bytes=uploaded_file.size,
            processing_status='PROCESSING',
            started_at=timezone.now()
        )

        try:
            # Validate upload
            self.validate_upload(uploaded_file)

            # Process image
            with Image.open(uploaded_file) as img:
                # Remove EXIF data for privacy
                img = ImageOps.exif_transpose(img)  # Rotate based on EXIF, then remove
                clean_img = Image.new(img.mode, img.size)
                clean_img.putdata(list(img.getdata()))

                # Generate thumbnails
                thumbnails = self.generate_thumbnails(clean_img, user_profile.user.id)

                # Upload to storage
                storage_urls = self.upload_to_storage(thumbnails, user_profile.user.id)

                # Update profile
                user_profile.photo_thumbnails = storage_urls
                user_profile.photo_uploaded_at = timezone.now()
                user_profile.photo_processing_status = 'COMPLETED'
                user_profile.save()

                # Update job
                job.processing_status = 'COMPLETED'
                job.completed_at = timezone.now()
                job.thumbnails_created = storage_urls
                job.cdn_urls = self.generate_cdn_urls(storage_urls)
                job.save()

                return storage_urls

        except Exception as e:
            job.processing_status = 'FAILED'
            job.error_message = str(e)
            job.completed_at = timezone.now()
            job.save()

            user_profile.photo_processing_status = 'FAILED'
            user_profile.save()

            raise

    def generate_thumbnails(self, image, user_id):
        """Generate multiple thumbnail sizes"""
        thumbnails = {}

        for size_name, dimensions in self.THUMBNAIL_SIZES.items():
            # Create thumbnail maintaining aspect ratio
            thumb = image.copy()
            thumb.thumbnail(dimensions, Image.Resampling.LANCZOS)

            # Create square crop from center if needed
            if thumb.width != thumb.height:
                size = min(thumb.width, thumb.height)
                left = (thumb.width - size) / 2
                top = (thumb.height - size) / 2
                right = (thumb.width + size) / 2
                bottom = (thumb.height + size) / 2
                thumb = thumb.crop((left, top, right, bottom))

            thumbnails[size_name] = thumb

        return thumbnails

    def upload_to_storage(self, thumbnails, user_id):
        """Upload thumbnails to cloud storage"""
        urls = {}

        for size_name, image in thumbnails.items():
            # Generate filename
            filename = f"profile_photos/{user_id}/{size_name}_{timezone.now().strftime('%Y%m%d_%H%M%S')}.webp"

            # Convert to WebP for better compression
            output = BytesIO()
            image.save(output, format='WEBP', quality=self.QUALITY_SETTINGS['WEBP'])
            output.seek(0)

            if self.storage_backend == 's3':
                # Upload to S3
                self.s3_client.upload_fileobj(
                    output,
                    settings.AWS_STORAGE_BUCKET_NAME,
                    filename,
                    ExtraArgs={
                        'ContentType': 'image/webp',
                        'CacheControl': 'max-age=31536000',  # 1 year
                        'ACL': 'public-read'
                    }
                )
                urls[size_name] = f"https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{filename}"

        return urls

    def generate_cdn_urls(self, storage_urls):
        """Generate CDN URLs for better performance"""
        if not hasattr(settings, 'CDN_DOMAIN'):
            return storage_urls

        cdn_urls = {}
        for size_name, url in storage_urls.items():
            # Replace S3 domain with CDN domain
            cdn_urls[size_name] = url.replace(
                f"{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com",
                settings.CDN_DOMAIN
            )

        return cdn_urls
```

**Enhanced Photo Utilities:**
```python
# user_profile/utils.py (enhanced)
def get_profile_photo_url(user, size='medium', fallback_to_gravatar=True):
    """
    Enhanced photo URL generation with upload support
    Priority: Uploaded photo -> Gravatar -> Bootstrap icon
    """
    profile = getattr(user, 'profile', None)
    if not profile:
        return get_bootstrap_icon_url()

    # Check for uploaded photo
    if (profile.photo_thumbnails and
        profile.photo_processing_status == 'COMPLETED' and
        profile.photo_approved and
        size in profile.photo_thumbnails):
        return profile.photo_thumbnails[size]

    # Fall back to Gravatar if enabled
    if fallback_to_gravatar and profile.use_gravatar:
        gravatar_email = profile.gravatar_email or user.email
        if gravatar_email:
            return generate_gravatar_url(gravatar_email, get_size_pixels(size))

    # Final fallback to Bootstrap icon
    return get_bootstrap_icon_url()

def get_size_pixels(size_name):
    """Convert size name to pixel dimensions"""
    size_map = {
        'small': 75,
        'medium': 150,
        'large': 300,
        'xlarge': 500,
    }
    return size_map.get(size_name, 150)

def get_bootstrap_icon_url():
    """Generate Bootstrap icon URL for default avatar"""
    return '/static/icons/person-circle.svg'

def validate_image_file(file):
    """Django validator for image uploads"""
    processor = PhotoProcessor()
    try:
        processor.validate_upload(file)
    except ValidationError:
        raise  # Re-raise Django validation error
```

**Admin Interface Enhancements:**
```python
# user_profile/admin.py (enhanced)
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'roster_id', 'photo_status', 'photo_approved', 'created_at']
    list_filter = ['photo_approved', 'photo_processing_status', 'use_gravatar']
    search_fields = ['user__username', 'user__email', 'roster_id']
    readonly_fields = ['photo_thumbnails', 'photo_uploaded_at', 'photo_processing_status']

    actions = ['approve_photos', 'reject_photos', 'reprocess_photos']

    def photo_status(self, obj):
        if obj.photo_thumbnails:
            status = obj.photo_processing_status
            approved = '✓' if obj.photo_approved else '✗'
            return f"{status} ({approved})"
        return "No photo"

    def approve_photos(self, request, queryset):
        """Bulk approve photos"""
        count = 0
        for profile in queryset:
            if profile.photo_thumbnails and not profile.photo_approved:
                profile.photo_approved = True
                profile.save()

                PhotoModerationLog.objects.create(
                    user_profile=profile,
                    moderator=request.user,
                    action='APPROVED'
                )
                count += 1

        self.message_user(request, f"Approved {count} photos.")

    def reject_photos(self, request, queryset):
        """Bulk reject photos"""
        count = 0
        for profile in queryset:
            if profile.photo_thumbnails and profile.photo_approved:
                profile.photo_approved = False
                profile.save()

                PhotoModerationLog.objects.create(
                    user_profile=profile,
                    moderator=request.user,
                    action='REJECTED'
                )
                count += 1

        self.message_user(request, f"Rejected {count} photos.")

@admin.register(PhotoProcessingJob)
class PhotoProcessingJobAdmin(admin.ModelAdmin):
    list_display = ['user_profile', 'processing_status', 'created_at', 'completed_at', 'file_size_mb']
    list_filter = ['processing_status', 'created_at']
    search_fields = ['user_profile__user__username', 'original_filename']
    readonly_fields = ['thumbnails_created', 'cdn_urls', 'error_message']

    def file_size_mb(self, obj):
        if obj.original_size_bytes:
            return f"{obj.original_size_bytes / 1024 / 1024:.1f} MB"
        return "Unknown"
```

**Frontend Photo Upload Interface:**
```javascript
// static/js/photo-upload.js
class PhotoUploader {
    constructor(uploadUrl, previewContainer) {
        this.uploadUrl = uploadUrl;
        this.previewContainer = document.querySelector(previewContainer);
        this.maxFileSize = 10 * 1024 * 1024; // 10MB
        this.allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];
        this.setupEventHandlers();
    }

    setupEventHandlers() {
        const fileInput = document.querySelector('#photo-upload');
        const dropZone = document.querySelector('.photo-drop-zone');

        fileInput.addEventListener('change', (e) => this.handleFileSelect(e));

        // Drag and drop support
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            this.handleFileSelect({ target: { files: e.dataTransfer.files } });
        });
    }

    handleFileSelect(event) {
        const files = Array.from(event.target.files);

        if (files.length === 0) return;

        const file = files[0];

        // Validate file
        if (!this.validateFile(file)) return;

        // Show preview
        this.showPreview(file);

        // Upload file
        this.uploadFile(file);
    }

    validateFile(file) {
        if (!this.allowedTypes.includes(file.type)) {
            this.showError('Please select a JPEG, PNG, or WebP image file.');
            return false;
        }

        if (file.size > this.maxFileSize) {
            this.showError('File size must be less than 10MB.');
            return false;
        }

        return true;
    }

    showPreview(file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const preview = document.querySelector('.photo-preview');
            preview.innerHTML = `
                <img src="${e.target.result}" alt="Preview" class="img-thumbnail" style="max-width: 200px;">
                <div class="progress mt-2">
                    <div class="progress-bar" role="progressbar" style="width: 0%"></div>
                </div>
            `;
        };
        reader.readAsDataURL(file);
    }

    uploadFile(file) {
        const formData = new FormData();
        formData.append('photo', file);
        formData.append('csrfmiddlewaretoken', this.getCSRFToken());

        const xhr = new XMLHttpRequest();

        // Upload progress
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                const progressBar = document.querySelector('.progress-bar');
                progressBar.style.width = percentComplete + '%';
            }
        });

        // Upload complete
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                this.handleUploadSuccess(response);
            } else {
                this.handleUploadError('Upload failed. Please try again.');
            }
        });

        xhr.addEventListener('error', () => {
            this.handleUploadError('Network error. Please check your connection.');
        });

        xhr.open('POST', this.uploadUrl);
        xhr.send(formData);
    }

    handleUploadSuccess(response) {
        // Update profile photo display
        const profilePhoto = document.querySelector('.current-profile-photo img');
        if (profilePhoto && response.photo_url) {
            profilePhoto.src = response.photo_url;
        }

        this.showSuccess('Photo uploaded successfully! It may take a moment to process.');

        // Poll for processing completion
        this.pollProcessingStatus(response.job_id);
    }

    pollProcessingStatus(jobId) {
        const pollInterval = setInterval(() => {
            fetch(`/user-profile/api/photo-jobs/${jobId}/`)
                .then(response => response.json())
                .then(data => {
                    if (data.processing_status === 'COMPLETED') {
                        clearInterval(pollInterval);
                        location.reload(); // Refresh to show processed photo
                    } else if (data.processing_status === 'FAILED') {
                        clearInterval(pollInterval);
                        this.showError('Photo processing failed. Please try again.');
                    }
                })
                .catch(() => {
                    clearInterval(pollInterval);
                });
        }, 2000);

        // Stop polling after 2 minutes
        setTimeout(() => clearInterval(pollInterval), 120000);
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    showError(message) {
        // Implementation depends on your notification system
        console.error(message);
    }

    showSuccess(message) {
        // Implementation depends on your notification system
        console.log(message);
    }
}

// Initialize uploader when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('#photo-upload')) {
        new PhotoUploader('/user-profile/api/upload-photo/', '.photo-preview-container');
    }
});
```

**API Endpoints:**
```python
# user_profile/api_views.py (enhanced)
class PhotoUploadView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser]

    def post(self, request):
        if 'photo' not in request.FILES:
            return Response({'error': 'No photo file provided'}, status=400)

        photo_file = request.FILES['photo']

        try:
            processor = PhotoProcessor()

            # Process photo asynchronously
            job = processor.process_profile_photo(request.user.profile, photo_file)

            return Response({
                'message': 'Photo uploaded successfully',
                'job_id': job.id,
                'processing_status': job.processing_status
            })

        except ValidationError as e:
            return Response({'error': str(e)}, status=400)
        except Exception as e:
            return Response({'error': 'Upload failed'}, status=500)

class PhotoJobStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        try:
            job = PhotoProcessingJob.objects.get(
                id=job_id,
                user_profile__user=request.user
            )

            serializer = PhotoJobSerializer(job)
            return Response(serializer.data)

        except PhotoProcessingJob.DoesNotExist:
            return Response({'error': 'Job not found'}, status=404)
```

**Background Tasks:**
```python
# user_profile/tasks.py
from celery import shared_task

@shared_task
def process_photo_async(user_profile_id, photo_path):
    """Process uploaded photo in background"""
    try:
        user_profile = UserProfile.objects.get(id=user_profile_id)
        processor = PhotoProcessor()

        with open(photo_path, 'rb') as photo_file:
            processor.process_profile_photo(user_profile, photo_file)

        # Clean up temporary file
        os.remove(photo_path)

    except Exception as e:
        logger.error(f"Photo processing failed for profile {user_profile_id}: {str(e)}")

@shared_task
def cleanup_old_photos():
    """Clean up old, unused photos from storage"""
    # Implementation for cleaning up old photos
    pass

@shared_task
def generate_photo_analytics():
    """Generate analytics on photo usage and processing"""
    # Implementation for analytics
    pass
```

**Implementation Plan:**

**Phase 1: Upload Validation and Basic Processing (Week 1)**
- Extend UserProfile model with photo fields
- Implement PhotoProcessor class with validation
- Create basic upload form and view
- Add PhotoProcessingJob model for tracking
- Implement admin interfaces for photo management

**Phase 2: Cloud Storage Integration and Thumbnails (Week 2)**
- Set up S3/CloudFlare R2 integration
- Implement thumbnail generation pipeline
- Add background task processing with Celery
- Create photo upload API endpoints
- Build responsive photo upload interface

**Phase 3: Admin Moderation Interface (Week 3)**
- Implement photo moderation workflow
- Create admin bulk operations for photo approval
- Add PhotoModerationLog for audit trail
- Build admin dashboard for photo management
- Implement photo flagging and review system

**Phase 4: CDN Integration and Performance Optimization (Week 4)**
- Configure CDN for optimal photo loading
- Implement photo caching strategies
- Add batch photo import capabilities
- Create photo analytics and reporting
- Performance optimization and monitoring

**Acceptance Criteria:**
- [ ] Users can upload photos with immediate preview and progress indication
- [ ] Photos processed and thumbnails generated within 30 seconds
- [ ] Admin can review and approve uploaded photos through bulk operations
- [ ] CDN delivers photos with <200ms load times globally
- [ ] Malicious file uploads blocked with proper error messages and user feedback
- [ ] Bulk photo import processes 100+ photos without system performance impact
- [ ] Mobile-responsive photo upload interface works on all devices
- [ ] Photo processing failures handled gracefully with user notification
- [ ] EXIF data removed from all uploaded photos for privacy protection
- [ ] Integration with existing Gravatar fallback system maintained

**Performance Requirements:**
- Photo upload and initial processing completes in <30 seconds
- Thumbnail generation for all sizes completes in <10 seconds
- CDN photo loading achieves <200ms globally
- Bulk photo operations support 100+ photos without timeout
- Storage costs optimized through WebP compression and cleanup policies

**Security Requirements:**
- File type validation prevents malicious uploads
- File size limits prevent storage abuse
- EXIF data removal protects user privacy
- Image content scanning for inappropriate material
- Secure cloud storage with proper access controls

**Testing Strategy:**
- Unit tests for photo processing pipeline and validation
- Integration tests for cloud storage upload and CDN delivery
- Load testing with concurrent photo uploads
- Security testing for malicious file upload prevention
- End-to-end testing of complete photo management workflow

**Dependencies:**
- Cloud storage account (AWS S3 or CloudFlare R2)
- CDN configuration for optimal delivery
- Background task processing (Celery + Redis)
- Image processing libraries (Pillow, pillow-heif)

**Estimated Effort:** 4 weeks

**Risk Mitigation:**
- Fallback to local storage if cloud storage unavailable
- Graceful degradation to Gravatar when photo processing fails
- Queue management for high-volume photo processing
- Storage quota monitoring and automated cleanup

## Technical Considerations

### Storage and Performance
- WebP format for optimal compression without quality loss
- Multiple thumbnail sizes for responsive design
- CDN integration for global photo delivery performance
- Automated cleanup policies for storage cost management

### Security and Privacy
- Comprehensive file validation to prevent malicious uploads
- EXIF data removal to protect user location privacy
- Admin moderation workflow for inappropriate content
- Secure cloud storage with proper access controls

### Integration Points
- Seamless integration with existing Gravatar fallback system
- Template component compatibility with current profile displays
- API endpoints ready for mobile app integration
- Analytics integration for photo usage tracking

This photo management system will provide NetEOC with professional-grade profile photo capabilities while maintaining security and performance standards essential for disaster response identification.
