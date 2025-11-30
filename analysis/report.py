import os

def generate_summary_text(edge_data, noise_data, hist_data, sharp_data, metric_data=None, art_data=None):
    """
    Generate a human-readable summary report.
    """
    lines = []
    lines.append("=== PyPic Editor Analysis Report ===")
    lines.append("==================================")
    lines.append("")
    
    # 1. Executive Summary
    lines.append("1. EXECUTIVE SUMMARY")
    lines.append("-" * 20)
    
    quality_change = "improved"
    if noise_data['noise_delta'] > 0: quality_change = "degraded (more noise)"
    if sharp_data['sharpness_delta'] < 0: quality_change = "softer/blurred"
    
    lines.append(f"The edited image appears to be {quality_change} compared to the original.")
    
    # Quick Stats
    lines.append(f"• Sharpness: {'Increased' if sharp_data['sharpness_delta'] > 0 else 'Decreased'}")
    lines.append(f"• Noise:     {'Increased' if noise_data['noise_delta'] > 0 else 'Decreased'}")
    lines.append(f"• Edges:     {'More Details' if edge_data['density_delta'] > 0 else 'Smoother'}")
    lines.append("")

    # 2. Detailed Metrics
    if metric_data:
        lines.append("2. QUALITY METRICS")
        lines.append("-" * 20)
        lines.append(f"• PSNR: {metric_data['psnr']:.2f} dB (Signal-to-Noise Ratio)")
        lines.append(f"• SSIM: {metric_data['ssim']:.4f} (Structural Similarity)")
        lines.append(f"• MSE:  {metric_data['mse']:.2f} (Error Magnitude)")
        lines.append("")
        
    # 3. Artifacts
    if art_data:
        lines.append("3. SIGNAL ANALYSIS")
        lines.append("-" * 20)
        lines.append(f"• Compression Artifacts: {art_data['compression']:.2f} (Lower is better)")
        lines.append(f"• Oversmoothing Risk:    {art_data['smoothing']:.2f}")
        lines.append("")

    # 4. Color & Tone
    lines.append("4. COLOR & TONE")
    lines.append("-" * 20)
    lines.append(f"• Brightness Delta: {hist_data['brightness_delta']:.2f}")
    lines.append(f"• Contrast Delta:   {hist_data['contrast_delta']:.2f}")
    lines.append(f"• Histogram Shift:  {hist_data['histogram_delta_score']:.2f}%")
    lines.append("")
    
    lines.append("End of Report")
    
    return "\n".join(lines)

def save_report_txt(text, filepath):
    with open(filepath, 'w') as f:
        f.write(text)
    return filepath
