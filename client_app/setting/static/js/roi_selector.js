class ROISelector {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.isDrawing = false;
        this.startX = 0;
        this.startY = 0;
        this.currentROI = null;
        this.roiList = [];
        this.imageScale = 1;
        this.imageOffsetX = 0;
        this.imageOffsetY = 0;
        this.image = null;
        this.selectedRoiIndex = -1;
        this.isDragging = false;
        this.dragStartX = 0;
        this.dragStartY = 0;
        this.originalRoi = null;
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.canvas.addEventListener('mousedown', this.handleMouseDown.bind(this));
        this.canvas.addEventListener('mousemove', this.handleMouseMove.bind(this));
        this.canvas.addEventListener('mouseup', this.handleMouseUp.bind(this));
        this.canvas.addEventListener('contextmenu', this.handleContextMenu.bind(this));
    }

    updateImageScale(scale, offsetX, offsetY) {
        this.imageScale = scale;
        this.imageOffsetX = offsetX;
        this.imageOffsetY = offsetY;
        this.draw();
    }

    getCanvasCoordinates(event) {
        const rect = this.canvas.getBoundingClientRect();
        const scaleX = this.canvas.width / rect.width;
        const scaleY = this.canvas.height / rect.height;
        return {
            x: (event.clientX - rect.left) * scaleX,
            y: (event.clientY - rect.top) * scaleY
        };
    }

    getImageCoordinates(canvasX, canvasY) {
        return {
            x: (canvasX - this.imageOffsetX) / this.imageScale,
            y: (canvasY - this.imageOffsetY) / this.imageScale
        };
    }

    handleMouseDown(event) {
        if (event.button === 0) { // 좌클릭
            const { x, y } = this.getCanvasCoordinates(event);
            
            // 이미지 영역 내에서만 드래그 시작
            if (x >= this.imageOffsetX && 
                x <= this.imageOffsetX + this.image.width * this.imageScale &&
                y >= this.imageOffsetY && 
                y <= this.imageOffsetY + this.image.height * this.imageScale) {
                
                const imageCoords = this.getImageCoordinates(x, y);
                this.isDrawing = true;
                this.startX = imageCoords.x;
                this.startY = imageCoords.y;
                this.currentROI = {
                    x: this.startX,
                    y: this.startY,
                    width: 0,
                    height: 0
                };
            }
        }
    }

    // 이미지 내부로 좌표를 clamp하는 함수 (한글 주석: ROI가 이미지 바깥으로 나가지 않도록 제한)
    clampToImage(x, y) {
        const maxX = this.image.width;
        const maxY = this.image.height;
        return {
            x: Math.max(0, Math.min(x, maxX)),
            y: Math.max(0, Math.min(y, maxY))
        };
    }

    handleMouseMove(event) {
        if (!this.isDrawing) return;

        const { x, y } = this.getCanvasCoordinates(event);
        let imageCoords = this.getImageCoordinates(x, y);
        // ROI가 이미지 바깥으로 나가지 않도록 clamp (한글 주석)
        imageCoords = this.clampToImage(imageCoords.x, imageCoords.y);

        this.currentROI.width = imageCoords.x - this.startX;
        this.currentROI.height = imageCoords.y - this.startY;

        this.draw();
    }

    handleMouseUp(event) {
        if (!this.isDrawing) return;

        const { x, y } = this.getCanvasCoordinates(event);
        let imageCoords = this.getImageCoordinates(x, y);
        // ROI가 이미지 바깥으로 나가지 않도록 clamp (한글 주석)
        imageCoords = this.clampToImage(imageCoords.x, imageCoords.y);

        this.currentROI.width = imageCoords.x - this.startX;
        this.currentROI.height = imageCoords.y - this.startY;

        // 최소 크기 체크
        if (Math.abs(this.currentROI.width) > 10 && Math.abs(this.currentROI.height) > 10) {
            // 음수 크기 보정
            if (this.currentROI.width < 0) {
                this.currentROI.x = this.startX + this.currentROI.width;
                this.currentROI.width = Math.abs(this.currentROI.width);
            }
            if (this.currentROI.height < 0) {
                this.currentROI.y = this.startY + this.currentROI.height;
                this.currentROI.height = Math.abs(this.currentROI.height);
            }
            // ROI가 이미지 바깥으로 나가지 않도록 clamp (한글 주석)
            const clamped = this.clampToImage(this.currentROI.x, this.currentROI.y);
            this.currentROI.x = clamped.x;
            this.currentROI.y = clamped.y;
            // width, height도 이미지 경계 내로 보정
            this.currentROI.width = Math.min(this.currentROI.width, this.image.width - this.currentROI.x);
            this.currentROI.height = Math.min(this.currentROI.height, this.image.height - this.currentROI.y);
            this.roiList.push(this.currentROI);
        }

        this.isDrawing = false;
        this.currentROI = null;
        this.draw();
    }

    handleContextMenu(event) {
        event.preventDefault();
        if (this.roiList.length > 0) {
            this.roiList.pop();
            this.draw();
        }
    }

    draw() {
        if (!this.image) return;

        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

        // 이미지 다시 그리기
        this.ctx.drawImage(
            this.image,
            this.imageOffsetX,
            this.imageOffsetY,
            this.image.width * this.imageScale,
            this.image.height * this.imageScale
        );

        // 현재 그리는 ROI
        if (this.currentROI) {
            this.ctx.strokeStyle = '#2563EB';
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(
                this.currentROI.x * this.imageScale + this.imageOffsetX,
                this.currentROI.y * this.imageScale + this.imageOffsetY,
                this.currentROI.width * this.imageScale,
                this.currentROI.height * this.imageScale
            );
        }

        // 저장된 ROI들
        this.roiList.forEach((roi, index) => {
            this.ctx.strokeStyle = this.selectedRoiIndex === this.roiList.indexOf(roi) ? '#DC2626' : '#2563EB';
            this.ctx.lineWidth = 2;
            this.ctx.strokeRect(
                roi.x * this.imageScale + this.imageOffsetX,
                roi.y * this.imageScale + this.imageOffsetY,
                roi.width * this.imageScale,
                roi.height * this.imageScale
            );
            
            // ROI 번호 표시
            this.ctx.fillStyle = '#2563EB';
            this.ctx.font = '14px Arial';
            this.ctx.fillText(
                `#${index + 1}`,
                roi.x * this.imageScale + this.imageOffsetX + 5,
                roi.y * this.imageScale + this.imageOffsetY + 20
            );
        });
    }

    async loadImage(url) {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => {
                this.image = img;
                resolve();
            };
            img.onerror = reject;
            img.src = url;
        });
    }

    getROICoords() {
        return this.roiList;
    }

    setROICoords(coords) {
        this.roiList = coords;
        this.draw();
    }

    clearROIs() {
        this.roiList = [];
        this.draw();
    }

    clearAll() {
        this.roiList = [];
        this.image = null;
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
} 